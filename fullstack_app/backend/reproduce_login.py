import requests
import json

API_URL = 'http://localhost:8000/api/login/'

def test_login(role, identifier, pin=None):
    payload = {'role': role, 'identifier': identifier}
    if pin:
        payload['pin'] = pin
    
    print(f"Testing login with: {payload}")
    try:
        response = requests.post(API_URL, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    # Test Admin Login
    test_login('admin', 'admin')
    
    # Test Farmer Login (valid phone)
    test_login('farmer', '01711111111')
    
    # Test Invalid Login
    test_login('admin', 'wrongpass')
