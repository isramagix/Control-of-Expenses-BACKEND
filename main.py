from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from database import Base, engine
from routers import auth, users, categories, transactions, budgets, reports, settings
import logging
import uvicorn
import time

# ======================================================
# 🔹 Configuración de logging
# ======================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================================
# 🔹 Crear las tablas si no existen
# ======================================================
Base.metadata.create_all(bind=engine)

# ======================================================
# 🔹 Inicialización de la app
# ======================================================
app = FastAPI(
    title="Control de Gastos API 💸",
    description="""
    ## API completa para gestión de gastos personales

    ### Características principales:
    - 🔐 **Autenticación JWT** con refresh tokens
    - 👤 **Gestión de usuarios** y perfiles
    - 📊 **Categorías personalizables** con iconos y colores
    - 💰 **Registro de gastos** con filtros avanzados
    - 📈 **Presupuestos** con alertas y períodos
    - 📊 **Reportes y analíticas** completas
    - ⚙️ **Configuraciones** personalizables
    
    ### Autenticación
    Para usar la API necesitas:
    1. Registrarte en `/api/auth/register`
    2. Hacer login en `/api/auth/login`
    3. Usar el `access_token` en el header: `Authorization: Bearer <token>`
    """,
    version="2.0.0",
    contact={
        "name": "Control de Gastos",
        "email": "support@controlgastos.com",
    },
    license_info={
        "name": "MIT",
    },
)

# ======================================================
# 🔹 Configurar CORS (para conexión con frontend)
# ======================================================
origins = [
    "http://localhost:5173",    # Vite (React/Vue)
    "http://localhost:3000",    # Create React App
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://localhost:4200",    # Angular
    "http://127.0.0.1:4200",
    # Agregar dominios de producción aquí
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ======================================================
# 🔹 Middleware para logging de requests
# ======================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log de la request
    logger.info(f"🔄 {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log de la response
    process_time = time.time() - start_time
    logger.info(f"✅ {request.method} {request.url} - {response.status_code} - {process_time:.3f}s")
    
    return response

# ======================================================
# 🔹 Manejo de excepciones globales
# ======================================================
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Error de validación",
            "errors": exc.errors(),
            "message": "Los datos proporcionados no son válidos"
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Recurso no encontrado",
            "message": f"La ruta {request.url.path} no existe"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"❌ Error interno del servidor: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "message": "Ha ocurrido un error inesperado. Por favor, intenta más tarde."
        }
    )

# ======================================================
# 🔹 Incluir todos los routers
# ======================================================

# Router de autenticación
app.include_router(auth.router)

# Router de usuarios
app.include_router(users.router)

# Router de categorías
app.include_router(categories.router)

# Router de gastos (transactions/expenses)
app.include_router(transactions.router)

# Router de presupuestos
app.include_router(budgets.router)

# Router de reportes y analíticas
app.include_router(reports.router)

# Router de configuraciones
app.include_router(settings.router)

# ======================================================
# 🔹 Rutas principales
# ======================================================
@app.get("/", tags=["🏠 General"])
def root():
    """Endpoint principal - Verificar que la API esté funcionando"""
    return {
        "message": "🚀 Control de Gastos API v2.0",
        "status": "online",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "auth": "/api/auth",
            "users": "/api/users", 
            "categories": "/api/categories",
            "expenses": "/api/expenses",
            "budgets": "/api/budgets",
            "reports": "/api/reports",
            "settings": "/api/settings"
        },
        "features": [
            "JWT Authentication",
            "User Management",
            "Expense Tracking", 
            "Budget Management",
            "Analytics & Reports",
            "User Settings"
        ]
    }

@app.get("/health", tags=["🏠 General"])
def health_check():
    """Health check endpoint para monitoreo"""
    try:
        # Verificar conexión a base de datos
        from database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2024-01-01T00:00:00Z"  # En producción usar datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.get("/version", tags=["🏠 General"])
def get_version():
    """Información de la versión de la API"""
    return {
        "version": "2.0.0",
        "release_date": "2024-01-01",
        "features": {
            "authentication": "JWT with refresh tokens",
            "database": "PostgreSQL with UUID primary keys",
            "api_framework": "FastAPI",
            "orm": "SQLAlchemy"
        }
    }

# ======================================================
# 🔹 Punto de entrada para desarrollo
# ======================================================
if __name__ == "__main__":
    import time
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Cambiar a True solo para desarrollo
        log_level="info"
    )
