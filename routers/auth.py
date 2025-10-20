from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from database import SessionLocal
from models.user import User
from models.user_settings import UserSettings
from schemas.user import UserCreate, UserResponse
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import uuid

# ========================
# 🔧 Configuración general
# ========================
SECRET_KEY = "clave_super_secreta_que_deberias_cambiar_en_produccion"
REFRESH_SECRET_KEY = "refresh_key_super_secreta_diferente"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter(prefix="/api/auth", tags=["🔐 Autenticación"])

# ========================
# 🔹 Dependencia DB
# ========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================
# 🔹 Funciones auxiliares
# ========================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_user_settings(user_id: uuid.UUID, db: Session):
    """Crear configuraciones por defecto para nuevo usuario"""
    settings = UserSettings(user_id=user_id)
    db.add(settings)
    db.commit()
    return settings

# ========================
# 🔹 Registro de usuario
# ========================
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Verificar duplicados
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    # Crear nuevo usuario
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        name=user.name,
        preferred_currency=user.preferred_currency,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Crear configuraciones por defecto
    create_user_settings(new_user.id, db)

    return new_user

# ========================
# 🔹 Login
# ========================
@router.post("/login")
def login(credentials: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == credentials.email).first()

    if not db_user or not verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Credenciales inválidas"
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta desactivada"
        )

    # Crear tokens
    user_data = {"sub": str(db_user.id)}
    access_token = create_access_token(data=user_data)
    refresh_token = create_refresh_token(data=user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

# ========================
# 🔹 Refresh Token
# ========================
@router.post("/refresh-token")
def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        # Crear nuevo access token
        user_data = {"sub": user_id}
        new_access_token = create_access_token(data=user_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# ========================
# 🔹 Logout (invalidar tokens)
# ========================
@router.post("/logout")
def logout():
    # En un sistema real, aquí se agregaría el token a una blacklist
    return {"message": "Logout exitoso"}

# ========================
# 🔹 Obtener usuario actual
# ========================
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user

# ========================
# 🔹 Info del usuario actual
# ========================
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
