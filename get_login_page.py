import requests

url = 'http://127.0.0.1:5000/auth/login'
response = requests.get(url)
print(f"Status Code: {response.status_code}")
print("\nResponse Headers:")
for key, value in response.headers.items():
    print(f"{key}: {value}")
print("\nResponse Content:")
print(response.text)
