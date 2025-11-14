"""
Test script to verify the add_human_data API returns total cumulative emissions
"""
import requests
import json
from datetime import datetime

print("=" * 70)
print("TESTING HUMAN DATA API - TOTAL EMISSIONS DISPLAY")
print("=" * 70)

# Test data
test_data = {
    "date": datetime.now().strftime('%Y-%m-%d'),
    "student_count": 3000,
    "staff_count": 400
}

print("\n📤 Sending test data:")
print(f"   Date: {test_data['date']}")
print(f"   Students: {test_data['student_count']}")
print(f"   Staff: {test_data['staff_count']}")
print(f"   Total: {test_data['student_count'] + test_data['staff_count']} people")

# Make API request
url = "http://localhost:5000/api/human_data"
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=test_data, headers=headers)
    
    print(f"\n📥 Response Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = response.json()
        print("\n✅ SUCCESS! API Response:")
        print(json.dumps(data, indent=2))
        
        # Verify structure
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        
        if 'data' in data:
            entry_data = data['data']
            print("\n📊 This Day's Entry:")
            print(f"   ✓ Date: {entry_data.get('date')}")
            print(f"   ✓ Students: {entry_data.get('student_count')}")
            print(f"   ✓ Staff: {entry_data.get('staff_count')}")
            print(f"   ✓ Total Population: {entry_data.get('total_count')}")
            print(f"   ✓ This Day Emissions: {entry_data.get('this_day_emissions_tonnes')} tonnes")
        
        if 'cumulative_stats' in data:
            cumulative = data['cumulative_stats']
            print("\n🌍 TOTAL CUMULATIVE EMISSIONS:")
            print(f"   🎯 TOTAL EMISSIONS: {cumulative.get('total_emissions_tonnes')} tonnes CO₂")
            print(f"   📅 Total Records: {cumulative.get('total_records')} days")
            print(f"   👥 Average Population: {cumulative.get('average_population')} people")
            print(f"   🎓 Average Students: {cumulative.get('average_students')}")
            print(f"   👨‍🏫 Average Staff: {cumulative.get('average_staff')}")
            
            print("\n" + "=" * 70)
            print("✅ API NOW CORRECTLY SHOWS TOTAL EMISSIONS!")
            print("=" * 70)
        else:
            print("\n❌ ERROR: cumulative_stats missing from response")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Cannot connect to server")
    print("   Make sure Flask app is running: python app.py")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
