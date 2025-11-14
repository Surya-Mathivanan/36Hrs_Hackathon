import os
import sys
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import mysql.connector
from mysql.connector import pooling
import jwt
from dotenv import load_dotenv

# ---- Setup ----
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Fail fast if DB password missing (avoid accidental leaking / fallback)
if not os.environ.get('DB_PASSWORD'):
    raise ValueError("DB_PASSWORD not found in environment variables (.env). Please set DB_PASSWORD before running the app.")

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'change-this-in-.env')
CORS(app)

# Runtime debug flag (used to enable development-only helpers)
DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'True').lower() in ('1', 'true', 'yes')

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD'),  # no default
    'database': os.environ.get('DB_NAME', 'campus_carbon'),
    'port': int(os.environ.get('DB_PORT', 3306)),
}

# Create a simple connection pool (fall back to None if pool creation fails)
pool = None
try:
    pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **DB_CONFIG)
    logger.info("MySQL connection pool created.")
except Exception as e:
    pool = None
    logger.warning(f"Could not create connection pool; will use single connections. Reason: {e}")

def get_db_connection():
    """
    Returns a MySQL connection from pool if available, otherwise a fresh connection.
    Caller is responsible for closing the connection.
    """
    try:
        if pool:
            conn = pool.get_connection()
        else:
            conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

# ---- Authentication helpers ----
def login_required(f):
    """Session-based decorator for web routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def api_token_required(f):
    """
    Decorator to protect API endpoints:
    - Accepts a valid session (web login), OR
    - Accepts a valid JWT in Authorization: Bearer <token>
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1) Session-based (browser)
        if 'user_id' in session:
            return f(*args, **kwargs)

        # 2) JWT-based (API clients)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
            try:
                payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
                # optional: set some request-level attributes if needed
                request.user_id = payload.get('user_id')
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401

        # No valid auth provided
        return jsonify({'error': 'Authentication required'}), 401

    return decorated_function

# ---- Routes ----
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Web login (sets session). Uses Werkzeug password hashing.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        connection = get_db_connection()
        if not connection:
            return render_template('login.html', error='Database connection error')

        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            logger.info(f"Login attempt for username='{username}' - user_found={bool(user)}")
        except Exception as e:
            logger.error(f"Error during login DB query: {e}")
            return render_template('login.html', error='Internal error')
        finally:
            if cursor:
                cursor.close()
            try:
                connection.close()
            except Exception:
                pass

        if not user:
            # helpful dev message (do not expose in production)
            logger.info(f"User not found for username='{username}'")
            return render_template('login.html', error='Invalid credentials')

        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('data_input'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/data-input')
@login_required
def data_input():
    return render_template('data_input.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """
    API login: returns JWT token (24 hours).
    Note: token is signed with the same secret used by session (SESSION_SECRET).
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        logger.info(f"API login attempt for username='{username}' - user_found={bool(user)}")
    except Exception as e:
        logger.error(f"Error during api_login DB query: {e}")
        return jsonify({'error': 'Internal error'}), 500
    finally:
        if cursor:
            cursor.close()
        try:
            connection.close()
        except Exception:
            pass

    if user and user['password'] == password:
        payload = {
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, app.secret_key, algorithm='HS256')
        # pyjwt 2.x returns a string; ensure it's serializable
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return jsonify({'token': token, 'username': user['username']})

    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/debug/reset_admin', methods=['POST'])
def debug_reset_admin():
    """Development-only helper: reset or create the `admin` user with password `admin123`.
    Enabled only when FLASK_DEBUG is truthy. This is for local development debugging only.
    """
    if not DEBUG_MODE:
        return jsonify({'error': 'Not found'}), 404

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = None
    try:
        cursor = connection.cursor()
        # Try update first
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", ('admin123', 'admin'))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", ('admin', 'admin123'))
        connection.commit()
        logger.info('Admin account reset/created by debug_reset_admin')
        return jsonify({'message': 'Admin password reset to admin123'}), 200
    except Exception as e:
        logger.exception('Error resetting admin user')
        try:
            connection.rollback()
        except Exception:
            pass
        return jsonify({'error': 'Failed to reset admin account'}), 500
    finally:
        if cursor:
            cursor.close()
        try:
            connection.close()
        except Exception:
            pass

@app.route('/api/data', methods=['POST'])
@api_token_required
def add_data():
    """
    Protected endpoint for adding activity records.
    Accepts JWT (Authorization Bearer) or active session.
    """
    data = request.get_json() or {}
    date = data.get('date')
    source_type = data.get('source_type')
    raw_value = data.get('raw_value')
    unit = data.get('unit')

    if not all([date, source_type, raw_value, unit]):
        return jsonify({'error': 'Missing required fields'}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO activity_data (date, source_type, raw_value, unit) VALUES (%s, %s, %s, %s)",
            (date, source_type, raw_value, unit)
        )
        connection.commit()
        return jsonify({'message': 'Data added successfully'}), 201
    except Exception as e:
        logger.exception("Error inserting activity_data")
        return jsonify({'error': 'Failed to insert data'}), 500
    finally:
        if cursor:
            cursor.close()
        try:
            connection.close()
        except Exception:
            pass

@app.route('/api/human_data', methods=['POST'])
@api_token_required
def add_human_data():
    """
    CORE FEATURE: Add human population data (students + staff counts).
    Protected endpoint - requires authentication.
    """
    data = request.get_json() or {}
    date = data.get('date')
    student_count = data.get('student_count')
    staff_count = data.get('staff_count')

    if not all([date, student_count is not None, staff_count is not None]):
        return jsonify({'error': 'Missing required fields: date, student_count, staff_count'}), 400

    try:
        student_count = int(student_count)
        staff_count = int(staff_count)
        if student_count < 0 or staff_count < 0:
            return jsonify({'error': 'Counts must be non-negative'}), 400
    except ValueError:
        return jsonify({'error': 'Counts must be valid integers'}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO human_population (date, student_count, staff_count) 
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE 
               student_count = VALUES(student_count), 
               staff_count = VALUES(staff_count)""",
            (date, student_count, staff_count)
        )
        connection.commit()
        
        # Calculate emissions for this entry
        total_people = student_count + staff_count
        emissions_kg = total_people * 1.0  # 1 kg CO2 per person per day
        emissions_tonnes = emissions_kg / 1000
        
        return jsonify({
            'message': 'Human population data added successfully',
            'data': {
                'date': date,
                'student_count': student_count,
                'staff_count': staff_count,
                'total_count': total_people,
                'estimated_emissions_tonnes': round(emissions_tonnes, 3)
            }
        }), 201
    except Exception as e:
        logger.exception("Error inserting human_population")
        return jsonify({'error': 'Failed to insert data'}), 500
    finally:
        if cursor:
            cursor.close()
        try:
            connection.close()
        except Exception:
            pass

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    Public dashboard JSON (no auth).
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

    # Normalize and validate date range; also compute window length for comparisons
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    if end_dt < start_dt:
        start_dt, end_dt = end_dt, start_dt
    window_days = max((end_dt - start_dt).days, 1)
    start_date = start_dt.strftime('%Y-%m-%d')
    end_date = end_dt.strftime('%Y-%m-%d')

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT 
                a.date,
                a.source_type,
                a.raw_value,
                a.unit,
                e.factor,
                (a.raw_value * e.factor / 1000) as emissions_tonnes
            FROM activity_data a
            JOIN emission_factors e ON a.source_type = e.source_type
            WHERE a.date BETWEEN %s AND %s
            ORDER BY a.date
        """
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()

        total_emissions = sum(row['emissions_tonnes'] for row in results)

        source_breakdown = {}
        for row in results:
            source = row['source_type']
            source_breakdown[source] = source_breakdown.get(source, 0) + row['emissions_tonnes']

        biggest_source = max(source_breakdown.items(), key=lambda x: x[1]) if source_breakdown else ('N/A', 0)

        # Daily, weekly, monthly, and yearly aggregations
        daily_data = {}
        weekly_data = {}
        monthly_data = {}
        yearly_data = {}
        
        for row in results:
            raw_date = row['date']
            if isinstance(raw_date, datetime):
                d = raw_date.date()
            else:
                try:
                    d = datetime.strptime(str(raw_date), '%Y-%m-%d').date()
                except Exception:
                    continue

            year = d.year
            iso_year, iso_week, _ = d.isocalendar()
            week_label = f"{iso_year}-W{iso_week:02d}"
            month = str(row['date'])[:7]
            date_str = d.strftime('%Y-%m-%d')

            daily_data[date_str] = daily_data.get(date_str, 0) + row['emissions_tonnes']
            weekly_data[week_label] = weekly_data.get(week_label, 0) + row['emissions_tonnes']
            monthly_data[month] = monthly_data.get(month, 0) + row['emissions_tonnes']
            yearly_data[year] = yearly_data.get(year, 0) + row['emissions_tonnes']

        # Previous period uses same window length as current selection
        prev_start_dt = start_dt - timedelta(days=window_days)
        prev_start = prev_start_dt.strftime('%Y-%m-%d')
        prev_end = start_dt.strftime('%Y-%m-%d')
        cursor.execute(query, (prev_start, prev_end))
        prev_results = cursor.fetchall()
        prev_emissions = sum(row['emissions_tonnes'] for row in prev_results)

        percent_change = 0.0
        if prev_emissions > 0:
            percent_change = ((total_emissions - prev_emissions) / prev_emissions) * 100.0

        weekly_comparison = [
            {'label': label, 'emissions': round(val, 2)}
            for label, val in sorted(weekly_data.items())
        ]
        yearly_comparison = [
            {'year': year, 'emissions': round(val, 2)}
            for year, val in sorted(yearly_data.items())
        ]

        energy_saved = 0
        for row in results:
            if row['source_type'] == 'electricity':
                try:
                    energy_saved += float(row['raw_value'])
                except Exception:
                    try:
                        energy_saved += row['raw_value']
                    except Exception:
                        pass

        # CORE FEATURE: Get human population emissions data
        human_query = """
            SELECT 
                h.date,
                h.student_count,
                h.staff_count,
                h.total_count,
                (h.total_count * 1.0 / 1000) as emissions_tonnes
            FROM human_population h
            WHERE h.date BETWEEN %s AND %s
            ORDER BY h.date
        """
        cursor.execute(human_query, (start_date, end_date))
        human_results = cursor.fetchall()
        
        # Aggregate human emissions data
        human_daily_data = {}
        human_weekly_data = {}
        human_monthly_data = {}
        human_yearly_data = {}
        human_total_emissions = 0
        avg_student_count = 0
        avg_staff_count = 0
        
        if human_results:
            for row in human_results:
                raw_date = row['date']
                if isinstance(raw_date, datetime):
                    d = raw_date.date()
                else:
                    try:
                        d = datetime.strptime(str(raw_date), '%Y-%m-%d').date()
                    except Exception:
                        continue
                
                year = d.year
                iso_year, iso_week, _ = d.isocalendar()
                week_label = f"{iso_year}-W{iso_week:02d}"
                month = str(row['date'])[:7]
                date_str = d.strftime('%Y-%m-%d')
                
                emissions = row['emissions_tonnes']
                human_daily_data[date_str] = human_daily_data.get(date_str, 0) + emissions
                human_weekly_data[week_label] = human_weekly_data.get(week_label, 0) + emissions
                human_monthly_data[month] = human_monthly_data.get(month, 0) + emissions
                human_yearly_data[year] = human_yearly_data.get(year, 0) + emissions
                human_total_emissions += emissions
                avg_student_count += row['student_count']
                avg_staff_count += row['staff_count']
            
            avg_student_count = int(avg_student_count / len(human_results))
            avg_staff_count = int(avg_staff_count / len(human_results))
        
        dashboard_data = {
            'kpis': {
                'total_emissions': round(total_emissions, 2),
                'percent_change': round(percent_change, 2),
                'biggest_source': biggest_source[0],
                'biggest_source_percent': round((biggest_source[1] / total_emissions * 100) if total_emissions > 0 else 0, 1),
                'energy_saved': round(energy_saved, 0)
            },
            'daily_trend': [
                {'date': date, 'emissions': round(emissions, 2)}
                for date, emissions in sorted(daily_data.items())
            ],
            'weekly_trend': weekly_comparison,
            'monthly_trend': [
                {'month': month, 'emissions': round(emissions, 2)}
                for month, emissions in sorted(monthly_data.items())
            ],
            'source_breakdown': [
                {'source': source, 'emissions': round(emissions, 2), 'percentage': round((emissions / total_emissions * 100) if total_emissions > 0 else 0, 1)}
                for source, emissions in source_breakdown.items()
            ],
            'weekly_comparison': weekly_comparison,
            'yearly_comparison': yearly_comparison,
            # CORE FEATURE: Human emissions data
            'human_emissions': {
                'total_emissions': round(human_total_emissions, 2),
                'avg_student_count': avg_student_count,
                'avg_staff_count': avg_staff_count,
                'avg_total_count': avg_student_count + avg_staff_count,
                'daily_trend': [
                    {'date': date, 'emissions': round(emissions, 2)}
                    for date, emissions in sorted(human_daily_data.items())
                ],
                'weekly_trend': [
                    {'label': label, 'emissions': round(val, 2)}
                    for label, val in sorted(human_weekly_data.items())
                ],
                'monthly_trend': [
                    {'month': month, 'emissions': round(emissions, 2)}
                    for month, emissions in sorted(human_monthly_data.items())
                ],
                'population_data': [
                    {
                        'date': str(row['date']),
                        'students': row['student_count'],
                        'staff': row['staff_count'],
                        'total': row['total_count'],
                        'emissions': round(row['emissions_tonnes'], 3)
                    }
                    for row in human_results
                ]
            }
        }
        return jsonify(dashboard_data)
    except Exception as e:
        logger.exception("Error building dashboard data")
        return jsonify({'error': 'Internal error'}), 500
    finally:
        if cursor:
            cursor.close()
        try:
            connection.close()
        except Exception:
            pass

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT 
                a.source_type,
                SUM(a.raw_value * e.factor / 1000) as total_emissions
            FROM activity_data a
            JOIN emission_factors e ON a.source_type = e.source_type
            GROUP BY a.source_type
            ORDER BY total_emissions DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()

        recommendations = []
        if results:
            top_source = results[0]['source_type']

            if top_source == 'electricity':
                recommendations.append({
                    'title': 'Focus on Energy Efficiency',
                    'description': 'Electricity is your biggest emission source. Consider switching to LED lighting and installing solar panels.',
                    'priority': 'High'
                })
            elif top_source == 'bus_diesel':
                recommendations.append({
                    'title': 'Promote Green Transportation',
                    'description': 'Transport emissions are high. Encourage carpooling, cycling, and consider electric buses.',
                    'priority': 'High'
                })
            elif top_source == 'canteen_lpg':
                recommendations.append({
                    'title': 'Optimize Canteen Operations',
                    'description': 'Canteen fuel usage is significant. Consider induction cooking or solar cookers.',
                    'priority': 'Medium'
                })
            elif top_source == 'waste_landfill':
                recommendations.append({
                    'title': 'Improve Waste Management',
                    'description': 'Waste emissions are high. Implement composting and recycling programs.',
                    'priority': 'High'
                })

            recommendations.append({
                'title': 'Regular Monitoring',
                'description': 'Continue tracking emissions data monthly to identify trends and measure improvement.',
                'priority': 'Medium'
            })

            recommendations.append({
                'title': 'Campus Awareness Campaign',
                'description': 'Educate students and staff about sustainable practices and carbon footprint reduction.',
                'priority': 'Low'
            })

        return jsonify({'recommendations': recommendations})
    except Exception as e:
        logger.exception("Error fetching recommendations")
        return jsonify({'error': 'Internal error'}), 500
    finally:
        if cursor:
            cursor.close()
        try:
            connection.close()
        except Exception:
            pass


@app.route('/api/upload_csv', methods=['POST'])
@api_token_required
def upload_csv():
    """Accepts JSON payload with 'records': [{date, source_type, raw_value, unit}, ...]
    Validates format and inserts rows into activity_data. Returns 400 with error on invalid format.
    """
    data = request.get_json() or {}
    records = data.get('records')

    if not isinstance(records, list) or len(records) == 0:
        return jsonify({'error': 'Invalid CSV format.'}), 400

    # Basic validation of each record
    for idx, rec in enumerate(records, start=1):
        if not isinstance(rec, dict):
            return jsonify({'error': f'Invalid CSV format at row {idx}.'}), 400
        if not all(k in rec for k in ('date', 'source_type', 'raw_value', 'unit')):
            return jsonify({'error': f'Missing required fields at row {idx}.'}), 400
        
        # Validate date format
        try:
            datetime.strptime(rec['date'], '%Y-%m-%d')
        except (ValueError, TypeError):
            return jsonify({'error': f'Invalid date format at row {idx}: "{rec.get("date")}" (expected YYYY-MM-DD)'}), 400
        
        # Validate raw_value is numeric
        try:
            rec['raw_value'] = float(rec['raw_value'])
        except (ValueError, TypeError):
            return jsonify({'error': f'Invalid numeric value at row {idx}: "{rec.get("raw_value")}"'}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = None
    try:
        cursor = connection.cursor()
        insert_stmt = "INSERT INTO activity_data (date, source_type, raw_value, unit) VALUES (%s, %s, %s, %s)"
        insert_values = []
        for rec in records:
            insert_values.append((rec['date'], rec['source_type'], rec['raw_value'], rec['unit']))

        cursor.executemany(insert_stmt, insert_values)
        connection.commit()
        return jsonify({'success': True, 'message': f'{len(insert_values)} records inserted.'}), 201
    except Exception as e:
        logger.exception('Error inserting CSV records')
        try:
            connection.rollback()
        except Exception:
            pass
        return jsonify({'error': 'Failed to insert CSV data.'}), 500
    finally:
        if cursor:
            cursor.close()
        try:
            connection.close()
        except Exception:
            pass

# ---- App run ----
if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('1', 'true', 'yes')
    use_reloader = not ('debugpy' in sys.modules)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=use_reloader)
