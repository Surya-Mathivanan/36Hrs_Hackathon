import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'campus_carbon'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'autocommit': False,
}

def init_database():
    """Initializes database schema, admin account, and sample data."""
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("📘 Connected to MySQL successfully!")

        # Step 1: Read and execute schema file
        print("📄 Reading schema file...")
        with open('database/schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Execute schema statements manually
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        for i, stmt in enumerate(statements, 1):
            try:
                cursor.execute(stmt)
                connection.commit()
            except Exception as e:
                print(f"⚠️ Warning on statement {i}: {e}")
                print(f"   Statement was: {stmt[:100]}...")

        print("✅ Database schema executed!\n")
        
        # Step 2: Verify emission_factors were inserted
        cursor.execute("SELECT COUNT(*) FROM emission_factors")
        ef_count = cursor.fetchone()[0]
        if ef_count == 0:
            print("⚠️ Emission factors table is empty! Inserting manually...")
            emission_factors_data = [
                ('electricity', 0.708, 'kg_co2e_per_kwh'),
                ('bus_diesel', 2.68, 'kg_co2e_per_liter'),
                ('canteen_lpg', 2.93, 'kg_co2e_per_kg'),
                ('waste_landfill', 1.25, 'kg_co2e_per_kg')
            ]
            for source_type, factor, factor_unit in emission_factors_data:
                cursor.execute(
                    "INSERT INTO emission_factors (source_type, factor, factor_unit) VALUES (%s, %s, %s)",
                    (source_type, factor, factor_unit)
                )
            connection.commit()
            print("✅ Emission factors inserted successfully!\n")
        else:
            print(f"✅ Emission factors table has {ef_count} entries\n")

        # Step 3: Create default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                ('admin', 'admin123')
            )
            connection.commit()
            print("✅ Default admin user created! (Username: admin | Password: admin123)\n")
        else:
            print("ℹ️ Admin user already exists.\n")

        # Step 4: Insert sample activity data if not already present
        sample_data = [
            ('2025-01-15', 'electricity', 120000, 'kWh'),
            ('2025-02-15', 'electricity', 115000, 'kWh'),
            ('2025-03-15', 'electricity', 118000, 'kWh'),
            ('2025-04-15', 'electricity', 122000, 'kWh'),
            ('2025-05-15', 'electricity', 125000, 'kWh'),
            ('2025-06-15', 'electricity', 130000, 'kWh'),
            ('2025-01-15', 'bus_diesel', 5000, 'Liters'),
            ('2025-02-15', 'bus_diesel', 4800, 'Liters'),
            ('2025-03-15', 'bus_diesel', 5200, 'Liters'),
            ('2025-04-15', 'bus_diesel', 5100, 'Liters'),
            ('2025-05-15', 'bus_diesel', 5300, 'Liters'),
            ('2025-06-15', 'bus_diesel', 5500, 'Liters'),
            ('2025-01-15', 'canteen_lpg', 800, 'kg'),
            ('2025-02-15', 'canteen_lpg', 750, 'kg'),
            ('2025-03-15', 'canteen_lpg', 820, 'kg'),
            ('2025-04-15', 'canteen_lpg', 810, 'kg'),
            ('2025-05-15', 'canteen_lpg', 830, 'kg'),
            ('2025-06-15', 'canteen_lpg', 850, 'kg'),
            ('2025-01-15', 'waste_landfill', 2000, 'kg'),
            ('2025-02-15', 'waste_landfill', 1900, 'kg'),
            ('2025-03-15', 'waste_landfill', 2100, 'kg'),
            ('2025-04-15', 'waste_landfill', 2050, 'kg'),
            ('2025-05-15', 'waste_landfill', 2200, 'kg'),
            ('2025-06-15', 'waste_landfill', 2300, 'kg'),
            ('2024-01-15', 'electricity', 110000, 'kWh'),
            ('2024-02-15', 'electricity', 108000, 'kWh'),
            ('2024-03-15', 'electricity', 112000, 'kWh'),
            ('2024-04-15', 'electricity', 115000, 'kWh'),
            ('2024-05-15', 'electricity', 118000, 'kWh'),
            ('2024-06-15', 'electricity', 120000, 'kWh'),
        ]

        cursor.execute("SELECT COUNT(*) FROM activity_data")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO activity_data (date, source_type, raw_value, unit) VALUES (%s, %s, %s, %s)",
                sample_data
            )
            connection.commit()
            print("✅ Sample data inserted successfully!\n")
        else:
            print("ℹ️ Sample data already exists.\n")

        # Step 5: Close connection
        cursor.close()
        connection.close()
        print("🎯 Database initialization completed successfully!")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("❌ Incorrect MySQL username or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("❌ Database not found.")
        else:
            print(f"❌ MySQL Error: {err}")
    except Exception as e:
        print(f"❌ General Error: {e}")

if __name__ == '__main__':
    init_database()
