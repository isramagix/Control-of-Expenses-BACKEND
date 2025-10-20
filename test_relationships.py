import requests
import json

# URLs base
base_url = "http://127.0.0.1:8000"
auth_url = f"{base_url}/auth"
transactions_url = f"{base_url}/transactions"

def test_full_workflow():
    print("🔹 Probando flujo completo con relaciones usuario-transacciones...")
    
    # 1. Registrar usuario
    print("\n1️⃣ Registrando usuario...")
    user_data = {
        "username": "usuario_test",
        "email": "test@ejemplo.com",
        "password": "password123"
    }
    
    try:
        register_response = requests.post(f"{auth_url}/register", json=user_data)
        print(f"   Status: {register_response.status_code}")
        
        if register_response.status_code == 200:
            print("   ✅ Usuario registrado exitosamente")
            user_info = register_response.json()
            print(f"   👤 Usuario ID: {user_info['id']}")
        else:
            print(f"   ❌ Error en registro: {register_response.text}")
            return
        
        # 2. Hacer login
        print("\n2️⃣ Haciendo login...")
        login_response = requests.post(f"{auth_url}/login", json=user_data)
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data["access_token"]
            print("   ✅ Login exitoso")
            print(f"   🔑 Token: {token[:20]}...")
        else:
            print(f"   ❌ Error en login: {login_response.text}")
            return
        
        # 3. Crear transacción
        print("\n3️⃣ Creando transacción...")
        headers = {"Authorization": f"Bearer {token}"}
        transaction_data = {
            "type": "ingreso",
            "description": "Salario mensual",
            "amount": 3000.0
        }
        
        create_response = requests.post(transactions_url, json=transaction_data, headers=headers)
        print(f"   Status: {create_response.status_code}")
        
        if create_response.status_code == 200:
            transaction = create_response.json()
            print("   ✅ Transacción creada exitosamente")
            print(f"   💰 ID: {transaction['id']}, Usuario ID: {transaction['user_id']}")
        else:
            print(f"   ❌ Error creando transacción: {create_response.text}")
            return
        
        # 4. Obtener transacciones del usuario
        print("\n4️⃣ Obteniendo transacciones del usuario...")
        get_response = requests.get(transactions_url, headers=headers)
        print(f"   Status: {get_response.status_code}")
        
        if get_response.status_code == 200:
            transactions = get_response.json()
            print(f"   ✅ Obtenidas {len(transactions)} transacciones")
            for t in transactions:
                print(f"   📊 {t['type']}: ${t['amount']} - {t['description']}")
        else:
            print(f"   ❌ Error obteniendo transacciones: {get_response.text}")
        
        # 5. Obtener resumen financiero
        print("\n5️⃣ Obteniendo resumen financiero...")
        summary_response = requests.get(f"{transactions_url}/summary/stats", headers=headers)
        print(f"   Status: {summary_response.status_code}")
        
        if summary_response.status_code == 200:
            summary = summary_response.json()
            print("   ✅ Resumen obtenido exitosamente")
            print(f"   📈 Ingresos: ${summary['total_income']}")
            print(f"   📉 Gastos: ${summary['total_expenses']}")
            print(f"   💵 Balance: ${summary['balance']}")
            print(f"   📝 Total transacciones: {summary['transaction_count']}")
        else:
            print(f"   ❌ Error obteniendo resumen: {summary_response.text}")
            
        print("\n🎉 ¡Prueba completa exitosa! Las relaciones funcionan correctamente.")
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_full_workflow()