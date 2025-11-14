import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME', 'campus_carbon')
)

cursor = conn.cursor()
cursor.execute("""
    INSERT INTO emission_factors (source_type, factor, factor_unit) 
    VALUES ('human_daily', 1.0, 'kg_co2e_per_person_per_day') 
    ON DUPLICATE KEY UPDATE 
        factor = VALUES(factor), 
        factor_unit = VALUES(factor_unit)
""")
conn.commit()
print('✅ Emission factor added/updated successfully')
conn.close()
