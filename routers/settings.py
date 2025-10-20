from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User
from models.user_settings import UserSettings
from schemas.user_settings import UserSettingsUpdate, UserSettingsResponse
from routers.auth import get_current_user
from typing import Optional
from decimal import Decimal

router = APIRouter(prefix="/api/settings", tags=["Settings"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================
# 🔹 Obtener configuraciones del usuario
# ========================
@router.get("/", response_model=UserSettingsResponse)
def get_user_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las configuraciones del usuario actual"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        # Crear configuraciones por defecto si no existen
        settings = UserSettings(
            user_id=current_user.id,
            monthly_budget=Decimal('1000.00'),
            default_currency='EUR',
            budget_alert_percentage=80.0,
            email_notifications=True,
            push_notifications=True,
            weekly_reports=True,
            monthly_reports=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings

# ========================
# 🔹 Actualizar configuraciones
# ========================
@router.put("/", response_model=UserSettingsResponse)
def update_user_settings(
    settings_update: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar configuraciones del usuario"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        # Crear configuraciones si no existen
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    # Actualizar solo los campos proporcionados
    update_data = settings_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    return settings

# ========================
# 🔹 Configuración específica del presupuesto mensual
# ========================
@router.patch("/budget", response_model=UserSettingsResponse)
def update_monthly_budget(
    monthly_budget: Decimal,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar solo el presupuesto mensual"""
    if monthly_budget < 0:
        raise HTTPException(status_code=400, detail="El presupuesto debe ser positivo")
    
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    settings.monthly_budget = monthly_budget
    db.commit()
    db.refresh(settings)
    return settings

# ========================
# 🔹 Configuración de alertas
# ========================
@router.patch("/alerts", response_model=UserSettingsResponse)
def update_alert_settings(
    budget_alert_percentage: Optional[float] = None,
    email_notifications: Optional[bool] = None,
    push_notifications: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar configuraciones de alertas y notificaciones"""
    if budget_alert_percentage is not None and (budget_alert_percentage < 0 or budget_alert_percentage > 100):
        raise HTTPException(status_code=400, detail="El porcentaje de alerta debe estar entre 0 y 100")
    
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    if budget_alert_percentage is not None:
        settings.budget_alert_percentage = budget_alert_percentage
    if email_notifications is not None:
        settings.email_notifications = email_notifications
    if push_notifications is not None:
        settings.push_notifications = push_notifications
    
    db.commit()
    db.refresh(settings)
    return settings

# ========================
# 🔹 Configuración de reportes
# ========================
@router.patch("/reports", response_model=UserSettingsResponse)
def update_report_settings(
    weekly_reports: Optional[bool] = None,
    monthly_reports: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar configuraciones de reportes automáticos"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    if weekly_reports is not None:
        settings.weekly_reports = weekly_reports
    if monthly_reports is not None:
        settings.monthly_reports = monthly_reports
    
    db.commit()
    db.refresh(settings)
    return settings

# ========================
# 🔹 Configuración de moneda
# ========================
@router.patch("/currency", response_model=UserSettingsResponse)
def update_currency(
    currency: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar moneda predeterminada del usuario"""
    valid_currencies = ['EUR', 'USD', 'GBP']
    if currency not in valid_currencies:
        raise HTTPException(
            status_code=400, 
            detail=f"Moneda no válida. Opciones: {', '.join(valid_currencies)}"
        )
    
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    settings.default_currency = currency
    db.commit()
    db.refresh(settings)
    return settings

# ========================
# 🔹 Restablecer configuraciones por defecto
# ========================
@router.post("/reset", response_model=UserSettingsResponse)
def reset_to_default_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restablecer todas las configuraciones a sus valores por defecto"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    else:
        # Restablecer valores por defecto
        settings.monthly_budget = Decimal('1000.00')
        settings.default_currency = 'EUR'
        settings.budget_alert_percentage = 80.0
        settings.email_notifications = True
        settings.push_notifications = True
        settings.weekly_reports = True
        settings.monthly_reports = True
    
    db.commit()
    db.refresh(settings)
    return settings

# ========================
# 🔹 Eliminar configuraciones (usar valores por defecto)
# ========================
@router.delete("/")
def delete_user_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Eliminar configuraciones personalizadas (volverá a usar valores por defecto)"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if settings:
        db.delete(settings)
        db.commit()
        return {"message": "Configuraciones eliminadas. Se usarán valores por defecto."}
    
    return {"message": "No había configuraciones personalizadas."}

# ========================
# 🔹 Información de configuraciones disponibles
# ========================
@router.get("/options")
def get_settings_options():
    """Obtener las opciones disponibles para configuraciones"""
    return {
        "currencies": [
            {"code": "EUR", "name": "Euro", "symbol": "€"},
            {"code": "USD", "name": "US Dollar", "symbol": "$"},
            {"code": "GBP", "name": "British Pound", "symbol": "£"}
        ],
        "alert_percentages": [50, 60, 70, 80, 90, 95],
        "default_monthly_budget": 1000.00,
        "notification_types": [
            "email_notifications",
            "push_notifications",
            "weekly_reports",
            "monthly_reports"
        ]
    }