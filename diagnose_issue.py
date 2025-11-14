import requests
import sys
import os

print("=== DIAGNOSTIC REPORT ===\n")

# 1. Check current directory
print(f"1. Current directory: {os.getcwd()}")
print(f"   app.py exists: {os.path.exists('app.py')}")

# 2. Check if app.py has the route
if os.path.exists('app.py'):
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   'add_human_data' in app.py: {'def add_human_data' in content}")

# 3. Try importing
print("\n2. Testing import:")
try:
    sys.path.insert(0, os.getcwd())
    import app
    routes = [rule.endpoint for rule in app.app.url_map.iter_rules()]
    print(f"   Import successful")
    print(f"   'add_human_data' route registered: {'add_human_data' in routes}")
    print(f"   Total routes: {len(routes)}")
except Exception as e:
    print(f"   Import failed: {e}")

# 4. Test the running server
print("\n3. Testing running server at localhost:5000:")
try:
    response = requests.get("http://localhost:5000/api/dashboard", timeout=2)
    print(f"   Server is running (status: {response.status_code})")
    
    # Try to get the actual route
    response = requests.post("http://localhost:5000/api/human_data", json={"test": "data"})
    print(f"   /api/human_data response: {response.status_code}")
    
    if response.status_code == 404:
        print("\n   ❌ PROBLEM IDENTIFIED:")
        print("   The running Flask server does NOT have the human_data route")
        print("   This means:")
        print("   → You're running Flask from a DIFFERENT directory")
        print("   → OR there are MULTIPLE Flask instances running")
        print("   → OR Flask didn't restart properly")
except requests.exceptions.ConnectionError:
    print("   ❌ No server running on localhost:5000")
except Exception as e:
    print(f"   Error: {e}")

print("\n=== SOLUTION ===")
print("1. Find ALL running Flask/Python processes:")
print("   PowerShell: Get-Process python | Select-Object Id,Path")
print("\n2. Kill ALL Python processes:")
print("   PowerShell: Get-Process python | Stop-Process -Force")
print("\n3. Navigate to the correct directory:")
print(f"   cd '{os.getcwd()}'")
print("\n4. Start Flask fresh:")
print("   python app.py")
print("\n5. Look for this line in the output:")
print("   * Running on http://0.0.0.0:5000")
