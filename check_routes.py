import sys
sys.path.insert(0, '.')

try:
    from app import app
    
    print("=== Flask Routes ===\n")
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append((rule.endpoint, methods, str(rule)))
    
    # Sort and display
    for endpoint, methods, rule in sorted(routes, key=lambda x: x[2]):
        print(f"{methods:15} {rule:40} -> {endpoint}")
    
    # Check specifically for human_data
    print("\n=== Checking for human_data endpoint ===")
    human_routes = [r for r in routes if 'human' in r[0].lower() or 'human' in r[2].lower()]
    
    if human_routes:
        print("✅ Human data routes found:")
        for endpoint, methods, rule in human_routes:
            print(f"  {methods:15} {rule:40} -> {endpoint}")
    else:
        print("❌ NO human data routes found!")
        print("\nThis means the Flask app needs to be restarted or the route wasn't added correctly.")
    
except Exception as e:
    print(f"❌ Error loading app: {e}")
    import traceback
    traceback.print_exc()
