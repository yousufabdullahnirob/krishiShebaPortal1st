import requests
import json

BASE_URL = 'http://localhost:8000/api'

def verify_ml():
    # 1. Login
    print("Logging in...")
    login_payload = {
        'role': 'farmer',
        'identifier': '01711111111'
    }
    try:
        response = requests.post(f'{BASE_URL}/login/', json=login_payload)
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return
        
        data = response.json()
        token = data['token']
        print(f"Login successful. Token: {token}")
        
        # 2. Call Recommend Crop
        print("\nTesting Crop Recommendation...")
        headers = {'Authorization': f'Bearer {token}'}
        ml_payload = {
            'soil_type': 'clay',
            'season': 'kharif',
            'region': 'dhaka'
        }
        
        response = requests.post(f'{BASE_URL}/recommend-crop/', json=ml_payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ ML API Verification Successful!")
        else:
            print("\n❌ ML API Verification Failed!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    verify_ml()
