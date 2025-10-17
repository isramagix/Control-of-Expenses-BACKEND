import requests
import json

# Test del endpoint de registro
url = "http://127.0.0.1:8000/auth/register"
data = {
    "username": "testuser",
    "email": "test@example.com", 
    "password": "testpassword123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Registro exitoso!")
    else:
        print("❌ Error en el registro")
        
except Exception as e:
    print(f"❌ Error de conexión: {e}")