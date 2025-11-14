import mysql.connector
from dotenv import load_dotenv
import os
import requests

load_dotenv()

print("=== VERIFICATION TEST ===\n")

# 1. Check database
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME', 'campus_carbon')
)
cursor = conn.cursor(dictionary=True)

print("1. Database Check:")
cursor.execute("SELECT COUNT(*) as count FROM human_population")
count = cursor.fetchone()['count']
print(f"   Total records: {count}")

cursor.execute("SELECT date, student_count, staff_count, total_count FROM human_population ORDER BY date DESC LIMIT 3")
recent = cursor.fetchall()
print(f"   Most recent entries:")
for row in recent:
    print(f"     {row['date']}: {row['total_count']} people (Students: {row['student_count']}, Staff: {row['staff_count']})")

# Calculate expected emissions
cursor.execute("""
    SELECT 
        SUM(total_count) * 1.0 / 1000 as total_emissions,
        AVG(student_count) as avg_students,
        AVG(staff_count) as avg_staff
    FROM human_population
""")
stats = cursor.fetchone()
print(f"\n   Expected totals:")
print(f"     Total emissions: {float(stats['total_emissions']):.2f} tonnes")
print(f"     Avg students: {int(stats['avg_students'])}")
print(f"     Avg staff: {int(stats['avg_staff'])}")

conn.close()

# 2. Check API
print("\n2. API Check:")
try:
    response = requests.get("http://localhost:5000/api/dashboard")
    if response.status_code == 200:
        data = response.json()
        he = data.get('human_emissions', {})
        
        print(f"   API Status: ✅ Working")
        print(f"   Total emissions: {he.get('total_emissions', 'NOT FOUND')}")
        print(f"   Avg population: {he.get('avg_total_count', 'NOT FOUND')}")
        print(f"   Avg students: {he.get('avg_student_count', 'NOT FOUND')}")
        print(f"   Avg staff: {he.get('avg_staff_count', 'NOT FOUND')}")
        print(f"   Data points: {len(he.get('population_data', []))}")
        
        total_emissions = he.get('total_emissions', 0)
        # Convert to float if it's a string
        if isinstance(total_emissions, str):
            try:
                total_emissions = float(total_emissions)
            except ValueError:
                total_emissions = 0
        
        if total_emissions > 0:
            print("\n✅ SUCCESS: Data is flowing correctly!")
            print("   → Go to dashboard and press F5 to see the data")
        else:
            print("\n⚠️ WARNING: API returns 0 emissions")
    else:
        print(f"   API Status: ❌ Error {response.status_code}")
except Exception as e:
    print(f"   API Error: {e}")

print("\n=== NEXT STEPS ===")
print("1. Open: http://localhost:5000")
print("2. Press: Ctrl + Shift + R (hard refresh)")
print("3. Scroll to: 'Human CO₂ Emissions' section")
print("4. You should see your data!")
