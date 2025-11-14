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
        cursor = connection.cursor(dictionary=True)
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
        
        # Get total cumulative emissions from all records
        cursor.execute("""
            SELECT 
                SUM(total_count * 1.0 / 1000) as total_emissions,
                COUNT(*) as record_count,
                AVG(student_count) as avg_students,
                AVG(staff_count) as avg_staff
            FROM human_population
        """)
        stats = cursor.fetchone()
        
        total_emissions_all = float(stats['total_emissions'] or 0)
        record_count = stats['record_count'] or 0
        avg_students = int(stats['avg_students'] or 0)
        avg_staff = int(stats['avg_staff'] or 0)
        
        return jsonify({
            'message': 'Human population data added successfully',
            'data': {
                'date': date,
                'student_count': student_count,
                'staff_count': staff_count,
                'total_count': total_people,
                'this_day_emissions_tonnes': round(emissions_tonnes, 3)
            },
            'cumulative_stats': {
                'total_emissions_tonnes': round(total_emissions_all, 2),
                'total_records': record_count,
                'average_students': avg_students,
                'average_staff': avg_staff,
                'average_population': avg_students + avg_staff
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
        
        # Get emission breakdown
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
        
        # Get human emissions data
        cursor.execute("""
            SELECT 
                SUM(total_count * 1.0 / 1000) as total_emissions,
                AVG(total_count) as avg_population
            FROM human_population
        """)
        human_stats = cursor.fetchone()
        human_emissions = float(human_stats['total_emissions'] or 0)
        avg_population = int(human_stats['avg_population'] or 0)

        recommendations = []
        
        # Source-specific recommendations
        if results:
            top_source = results[0]['source_type']
            top_emissions = results[0]['total_emissions']

            if top_source == 'electricity':
                recommendations.append({
                'title': '⚡ Electricity: Your #1 Emission Source',
                'description': f'Electricity is your largest controllable emission source, contributing {top_emissions:.2f} tonnes CO₂. This is primarily driven by high-consumption devices like air conditioning, lighting, and lab equipment. Tackling this area is the single highest-impact action your campus can take.',
                'priority': 'High',
                'impact': 'High',
                'actionable_steps': [
                    'Conduct a professional energy audit to identify specific "hotspots" of wastage.',
                    'Replace all traditional bulbs (fluorescent, incandescent) with high-efficiency LED lighting (saves 75% energy per bulb).',
                    'Install motion sensors and timers in corridors, washrooms, and meeting rooms so lights are only on when needed.',
                    'Upgrade old air conditioners to new 5-star rated inverter models (can reduce AC energy use by 30-50%).',
                    'Set a campus-wide AC temperature policy (e.g., 24°C) to prevent overuse.',
                    'Aggressively pursue rooftop solar panel installation, starting with main academic blocks and hostels.',
                    'Implement a "Computers Off" policy at night, enforcing shutdown rather than sleep mode.',
                    'Install smart power strips on workstation clusters to completely cut power to peripherals (printers, monitors) after hours and eliminate phantom loads.'
                ],
                'expected_reduction': '30-50% reduction in electricity-based emissions',
                'cost': 'Medium to High (Initial) | High ROI (2-5 years)',
                'timeframe': '6-18 months for full implementation'
                })
            
            elif top_source == 'bus_diesel':
                recommendations.append({
                'title': '🚌 Transportation: High Carbon Footprint',
                'description': f'Campus-owned diesel transport contributes {top_emissions:.2f} tonnes CO₂. These vehicles are a major source of not only CO2 but also harmful local air pollutants (PM2.5). A planned transition to cleaner transport is crucial for both carbon goals and campus health.',
                'priority': 'High',
                'impact': 'High',
                'actionable_steps': [
                    'Develop a 5-year plan to phase out diesel buses and replace them with electric buses.',
                    'Install EV charging stations in parking areas to support the transition (for buses, staff, and student vehicles).',
                    'Optimize bus routes using software to reduce total kilometers traveled and minimize engine idle time.',
                    'Implement a campus bike-sharing program with dedicated bike racks at key locations (hostels, canteen, main gate).',
                    'Create dedicated, safe cycling lanes within the campus to encourage biking over private vehicles.',
                    'Promote a carpooling platform/app for students and staff commuting from the city.',
                    'Enforce a "No-Idling" zone policy for all vehicles on campus.',
                    'Partner with public transport authorities to improve bus frequency to the campus gate.'
                ],
                'expected_reduction': '40-60% reduction in transport emissions (up to 90% with full EV transition)',
                'cost': 'High (Vehicle purchase) | Medium (Fuel savings offset cost)',
                'timeframe': '1-3 years for fleet transition'
                })
            
            elif top_source == 'canteen_lpg':
                recommendations.append({
                'title': '🍳 Canteen: Optimize Cooking Operations',
                'description': f'Canteen LPG (a fossil fuel) contributes {top_emissions:.2f} tonnes CO₂. This is a consistent, daily emission source. Modern, efficient electric alternatives like induction are not only cleaner (especially when paired with solar) but also safer and improve indoor air quality for kitchen staff.',
                'priority': 'Medium',
                'impact': 'Medium',
                'actionable_steps': [
                    'Phase out LPG stoves and replace them with commercial-grade induction cooktops, which are ~85% efficient (vs. LPG at ~40%).',
                    'Install solar cookers or solar water heating systems for large-scale water boiling (e.g., for rice, tea).',
                    'Utilize pressure cookers for items like dals and legumes to reduce cooking time by up to 70%.',
                    'Implement a "Menu Engineering" policy to batch-cook popular items, reducing stop-start energy waste.',
                    'Conduct regular maintenance on all kitchen equipment (gaskets, burners) to ensure optimal efficiency.',
                    'Explore setting up a campus biogas plant to convert food waste into methane for cooking, creating a circular system.',
                    'Source produce from local farms to reduce the "Scope 3" emissions embedded in your food supply chain.'
                ],
                'expected_reduction': '25-40% reduction in cooking-related emissions',
                'cost': 'Low to Medium',
                'timeframe': '3-9 months'
                })
            
            elif top_source == 'waste_landfill':
                recommendations.append({
                'title': '♻️ Waste: Implement Zero-Waste Campus',
                'description': f'Waste sent to landfills generates {top_emissions:.2f} tonnes CO₂ (as methane). Methane (CH4) is a greenhouse gas over 25 times more potent than CO₂. A "Zero-Waste" approach, focusing on the 3 R\'s (Reduce, Reuse, Recycle), can drastically cut this.',
                'priority': 'High',
                'impact': 'High',
                'actionable_steps': [
                    'Conduct a "waste audit" (sorting a day\'s waste) to identify your main waste streams (e.g., plastic, paper, food).',
                    'Implement a mandatory 3-bin segregation system campus-wide: Organic (food), Recyclable (paper, plastic, metal), and Landfill (other).',
                    'Start an on-campus composting program for all food waste from canteens and hostels. Use the compost for campus landscaping.',
                    'Aggressively ban all single-use plastics (cups, plates, straws) in canteens and for all campus events.',
                    'Install water refill stations across the campus to eliminate the need for single-use plastic water bottles.',
                    'Set up a "Reuse Store" where students can donate or take items like books, electronics, and clothes at the end of the semester.',
                    'Partner with local recycling vendors for efficient collection of segregated paper, plastic, and e-waste.',
                    'Set double-sided printing as the default on all campus computers and printers.'
                ],
                'expected_reduction': '50-70% reduction in landfill-bound waste and associated emissions',
                'cost': 'Low (Primarily operational and awareness-based)',
                'timeframe': '2-4 months to implement fully'
                })

        # Human emissions recommendations
        if human_emissions > 0:
            recommendations.append({
                'title': '👥 Human CO₂: An Indirect Factor',
            'description': f'The campus population (avg. {avg_population} people) contributes {human_emissions:.2f} tonnes CO₂ from respiration. This is a natural biological process and part of the "short-term carbon cycle." Unlike burning fossil fuels (which releases "long-term" carbon), this is not a target for direct reduction. However, a larger population *indirectly* increases emissions from energy, transport, and waste.',
            'priority': 'Low',
            'impact': 'Low (Natural Process)',
            'actionable_steps': [
                'Note: Do not focus on reducing this number directly. It is a natural process.',
                'Use this population data to inform indirect emission strategies (e.g., "emissions per student").',
                'Implement hybrid learning/work models to slightly reduce daily on-campus density, which in turn cuts transport and energy use.',
                'Stagger class and lab timings to prevent peak-hour congestion for both transport and canteen services.',
                'Focus on reducing the *per-person* carbon footprint (total emissions / avg_population) rather than the respiration footprint.'
            ],
            'expected_reduction': 'N/A (Focus is on indirect reductions)',
            'cost': 'N/A',
            'timeframe': 'Ongoing'
            })

        # General recommendations (always included)
        recommendations.extend([
            {
                'title': '📊 Data-Driven Decision Making',
            'description': 'You cannot manage what you do not measure. This analyzer provides the real-time data needed to move from guessing to targeted, effective action. Use this data to prove what works, justify investments (like solar), and hold departments accountable.',
            'priority': 'High',
            'impact': 'High (Enabler)',
            'actionable_steps': [
                'Monitor this dashboard daily. Identify any sudden spikes and investigate the cause.',
                'Set a clear, public monthly reduction target (e.g., "Reduce electricity use by 5% this month").',
                'Generate quarterly reports from this data to share with management and the student council.',
                'Use the data to benchmark your campus against other institutions or national averages.',
                'Create department-level dashboards to foster friendly competition on reduction goals.'
            ],
            'expected_reduction': 'Enables an additional 20-30% reduction through targeted strategies',
            'cost': 'Free (using this platform)',
                'timeframe': 'Ongoing'
            },
            {
                'title': '🌱 Green Campus Initiative',
            'description': 'Technology and infrastructure are only half the solution. A successful carbon reduction plan requires buy-in and active participation from every student and staff member. A "Green Campus" culture makes sustainability the default, not the exception.',
            'priority': 'Medium',
            'impact': 'High (Long-term)',
            'actionable_steps': [
                'Form a "Green Team" or "Sustainability Council" with student and staff volunteers from all departments.',
                'Conduct monthly awareness campaigns, workshops, and guest lectures on sustainability topics.',
                'Organize large-scale tree plantation drives on campus (focus on native species) to create a carbon sink.',
                'Display real-time emission data from this dashboard on public screens in the canteen and library.',
                'Integrate sustainability modules into first-year orientation and relevant academic courses.',
                'Partner with academic departments to use the campus as a "Living Lab" for sustainability research projects.',
                'Reward departments and hostels that achieve the highest emission reductions each semester.'
            ],
            'expected_reduction': '15-25% reduction through behavioral change',
            'cost': 'Low',
                'timeframe': '3-6 months to establish'
            },
            {
                'title': '🏛️ Infrastructure Upgrades (Long-Term Vision)',
            'description': 'These are high-cost, high-impact capital projects that lock in sustainability and savings for decades. They should be integrated into the campus\'s long-term master plan and budget cycle.',
            'priority': 'Medium',
            'impact': 'Very High',
            'actionable_steps': [
                'Develop a "Green Building" policy for all new constructions, targeting GRIHA or LEED certification.',
                'Install campus-wide rainwater harvesting systems to reduce reliance on municipal water and save energy on pumping.',
                'Upgrade to centralized, energy-efficient HVAC systems with smart zoning controls.',
                'Create green roofs and vertical gardens on buildings to improve insulation and reduce cooling loads.',
                'Install smart meters for electricity and water at the building-level for granular data tracking.',
                'Retrofit old buildings with better insulation and double-glazed windows to reduce heat gain.'
            ],
            'expected_reduction': '30-40% long-term reduction on new/retrofitted infrastructure',
            'cost': 'High (Capital Expenditure)',
                'timeframe': '1-5 years (Phased)'
            },
            {
                'title': '⭐ Quick Wins: Immediate Actions',
            'description': 'Build momentum and show immediate progress with these simple, low-cost actions. These wins are highly visible and help build the cultural support needed for larger, more expensive projects.',
            'priority': 'High',
            'impact': 'Medium',
            'actionable_steps': [
                'TODAY: Mandate that all classroom projectors, lights, and fans are turned off by the last person leaving.',
                'THIS WEEK: Set all network printers to double-sided printing by default.',
                'THIS WEEK: Launch a "phantom load" campaign, encouraging unplugging chargers and devices when not in use.',
                'THIS MONTH: Place "Save Energy / Save Water" stickers on all switches and taps.',
                'THIS MONTH: Designate student "Energy Monitors" for each floor/department to ensure compliance after hours.',
                'THIS MONTH: Start the paper recycling program by placing collection boxes in all offices and classrooms.'
            ],
            'expected_reduction': '10-15% immediate reduction from low-hanging fruit',
            'cost': 'Very Low',
                'timeframe': 'Immediate to 1 month'
            }
        ])

        return jsonify({
            'recommendations': recommendations,
            'summary': {
                'total_recommendations': len(recommendations),
                'high_priority': len([r for r in recommendations if r['priority'] == 'High']),
                'estimated_total_reduction': '50-70% achievable with full implementation',
                'message': 'Start with "Quick Wins" and "High Priority" items for maximum immediate impact!'
            }
        })
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

@app.route('/api/human_cumulative_stats', methods=['GET'])
def get_human_cumulative_stats():
    """
    Get all-time cumulative statistics for human emissions.
    Returns total emissions, record count, and averages across ALL data.
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                SUM(total_count * 1.0 / 1000) as total_emissions,
                COUNT(*) as record_count,
                AVG(student_count) as avg_students,
                AVG(staff_count) as avg_staff
            FROM human_population
        """)
        stats = cursor.fetchone()
        
        total_emissions = float(stats['total_emissions'] or 0)
        record_count = stats['record_count'] or 0
        avg_students = int(stats['avg_students'] or 0)
        avg_staff = int(stats['avg_staff'] or 0)
        
        return jsonify({
            'total_emissions': round(total_emissions, 2),
            'total_records': record_count,
            'average_students': avg_students,
            'average_staff': avg_staff,
            'average_population': avg_students + avg_staff
        })
    except Exception as e:
        logger.exception("Error fetching cumulative stats")
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
