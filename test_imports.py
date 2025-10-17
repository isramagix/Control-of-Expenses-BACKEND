try:
    print("Importando database...")
    from database import SessionLocal
    print("✅ database importado")
    
    print("Importando models.user...")
    from models.user import User
    print("✅ User model importado")
    
    print("Importando schemas.user...")
    from schemas.user import UserCreate
    print("✅ UserCreate schema importado")
    
    print("Probando conexión a DB...")
    db = SessionLocal()
    print("✅ Sesión de DB creada")
    db.close()
    print("✅ Sesión cerrada correctamente")
    
    print("Probando funciones de password...")
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    test_hash = pwd_context.hash("testpassword")
    print(f"✅ Hash generado: {test_hash[:20]}...")
    
    print("✅ Todos los imports y funciones básicas funcionan")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()