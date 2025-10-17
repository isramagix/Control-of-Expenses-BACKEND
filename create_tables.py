from database import Base, engine
from models.user import User
from models.transactions import Transaction

print("🔹 Creando tablas en la base de datos...")

try:
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")
    
    # Verificar conexión
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✅ Conexión a la base de datos exitosa")
        
except Exception as e:
    print(f"❌ Error: {e}")