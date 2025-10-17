from database import engine

try:
    with engine.connect() as conn:
        print("✅ Conexión exitosa a la base de datos ControlGastos")
except Exception as e:
    print("❌ Error de conexión:", e)
