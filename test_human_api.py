import requests
from datetime import datetime

# Test the human_data API endpoint
print("=== Testing Human Population API ===\n")

base_url = "http://localhost:5000"

# Step 1: Login to get session cookie
print("1. Logging in as admin...")
login_response = requests.post(
    f"{base_url}/login",
    data={"username": "admin", "password": "admin123"},
    allow_redirects=False
)

if login_response.status_code in [200, 302]:
    print("   ✅ Login successful")
    session_cookie = login_response.cookies
else:
    print(f"   ❌ Login failed: {login_response.status_code}")
    exit(1)

# Step 2: Test human_data endpoint
print("\n2. Testing /api/human_data endpoint...")
test_data = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "student_count": 5000,
    "staff_count": 500
}

response = requests.post(
    f"{base_url}/api/human_data",
    json=test_data,
    cookies=session_cookie
)

print(f"   Status Code: {response.status_code}")
print(f"   Response: {response.text[:200]}")

if response.status_code == 201:
    print("\n   ✅ SUCCESS! API is working correctly")
    data = response.json()
    print(f"   Message: {data.get('message')}")
    if 'data' in data:
        print(f"   Total Count: {data['data'].get('total_count')}")
        print(f"   Emissions: {data['data'].get('estimated_emissions_tonnes')} tonnes")
elif response.status_code == 404:
    print("\n   ❌ ERROR 404: Endpoint not found")
    print("   → Your Flask app needs to be RESTARTED")
    print("   → Stop the current Flask app (Ctrl+C)")
    print("   → Run: python app.py")
elif response.status_code == 401:
    print("\n   ❌ ERROR 401: Authentication required")
    print("   → Session cookie might be invalid")
else:
    print(f"\n   ❌ ERROR {response.status_code}")
    print(f"   Response: {response.text}")

print("\n=== Test Complete ===")
