from database import engine
from sqlalchemy import text

# Conectar y eliminar todas las tablas
with engine.connect() as conn:
    # Obtener todas las tablas
    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
    tables = [row[0] for row in result]
    
    if tables:
        # Eliminar todas las tablas
        for table in tables:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
        conn.commit()
        print(f'✅ Eliminadas {len(tables)} tablas existentes')
    else:
        print('✅ No había tablas que eliminar')