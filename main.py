from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import auth, transactions

# ======================================================
# 🔹 Crear las tablas si no existen
# ======================================================
Base.metadata.create_all(bind=engine)

# ======================================================
# 🔹 Inicialización de la app
# ======================================================
app = FastAPI(title="Control de Gastos API 💸")

# ======================================================
# 🔹 Configurar CORS (para conexión con React)
# ======================================================
origins = [
    "http://localhost:5173",  # Vite
    "http://localhost:3000",  # CRA
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# 🔹 Routers
# ======================================================
app.include_router(auth.router)
app.include_router(transactions.router)

# ======================================================
# 🔹 Ruta raíz
# ======================================================
@app.get("/")
def root():
    return {"message": "🚀 API de Control de Gastos funcionando correctamente"}
