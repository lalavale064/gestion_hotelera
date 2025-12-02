import sys
sys.path.insert(0, '.')

from app import app, get_conn
from datetime import date, timedelta

# Test the occupancy report endpoint
with app.test_client() as client:
    # Set headers to simulate admin user
    headers = {'X-User-Role': 'admin'}
    
    # Test 1: Basic occupancy report (JSON)
    print("Testing /api/reports/occupancy...")
    response = client.get('/api/reports/occupancy', headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.get_json()}")
    print()
    
    # Test 2: Occupancy CSV
    print("Testing /api/reports/occupancy/csv...")
    today = date.today()
    start = today.replace(day=1)
    response = client.get(f'/api/reports/occupancy/csv?start_date={start}', headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("CSV generated successfully")
        print(f"First 200 chars: {response.data[:200]}")
    else:
        print(f"Error: {response.data}")
    print()
    
    # Test 3: Export report
    print("Testing /api/reports/export?type=reservations...")
    response = client.get('/api/reports/export?type=reservations', headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("CSV generated successfully")
        print(f"First 200 chars: {response.data[:200]}")
    else:
        print(f"Error: {response.data}")
