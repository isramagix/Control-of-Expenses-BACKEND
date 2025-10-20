from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
from models.user import User
from models.category import Category
from models.transactions import Expense
from models.budget import Budget
from schemas.user import UserUpdate, UserProfile
from routers.auth import get_current_user
import json

router = APIRouter(prefix="/api/users", tags=["👤 Usuarios"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================
# 🔹 Obtener perfil del usuario
# ========================
@router.get("/profile", response_model=UserProfile)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Calcular estadísticas del perfil
    total_expenses = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == current_user.id
    ).scalar()
    
    total_categories = db.query(func.count(Category.id)).filter(
        Category.user_id == current_user.id
    ).scalar()
    
    active_budgets = db.query(func.count(Budget.id)).filter(
        Budget.user_id == current_user.id
    ).scalar()
    
    # Crear respuesta con estadísticas
    user_profile = UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        preferred_currency=current_user.preferred_currency,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        total_expenses=float(total_expenses or 0),
        total_categories=total_categories or 0,
        active_budgets=active_budgets or 0
    )
    
    return user_profile

# ========================
# 🔹 Actualizar perfil del usuario
# ========================
@router.put("/profile", response_model=UserProfile)
def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar si el email ya existe (si se está cambiando)
    if user_update.name is not None:
        current_user.name = user_update.name
    
    if user_update.preferred_currency is not None:
        current_user.preferred_currency = user_update.preferred_currency
    
    db.commit()
    db.refresh(current_user)
    
    # Recalcular estadísticas
    total_expenses = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == current_user.id
    ).scalar()
    
    total_categories = db.query(func.count(Category.id)).filter(
        Category.user_id == current_user.id
    ).scalar()
    
    active_budgets = db.query(func.count(Budget.id)).filter(
        Budget.user_id == current_user.id
    ).scalar()
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        preferred_currency=current_user.preferred_currency,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        total_expenses=float(total_expenses or 0),
        total_categories=total_categories or 0,
        active_budgets=active_budgets or 0
    )

# ========================
# 🔹 Eliminar cuenta
# ========================
@router.delete("/account")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Marcar como inactivo en lugar de eliminar (soft delete)
    current_user.is_active = False
    db.commit()
    
    return {"message": "Cuenta desactivada exitosamente"}

# ========================
# 🔹 Exportar datos del usuario
# ========================
@router.post("/export-data")
def export_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Obtener todas las categorías del usuario
    categories = db.query(Category).filter(Category.user_id == current_user.id).all()
    
    # Obtener todos los gastos del usuario
    expenses = db.query(Expense).filter(Expense.user_id == current_user.id).all()
    
    # Obtener todos los presupuestos del usuario
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    
    # Crear estructura de datos para exportar
    export_data = {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "preferred_currency": current_user.preferred_currency,
            "created_at": current_user.created_at.isoformat(),
            "updated_at": current_user.updated_at.isoformat()
        },
        "categories": [
            {
                "id": str(cat.id),
                "name": cat.name,
                "icon": cat.icon,
                "color": cat.color,
                "created_at": cat.created_at.isoformat()
            } for cat in categories
        ],
        "expenses": [
            {
                "id": str(exp.id),
                "category_id": str(exp.category_id),
                "description": exp.description,
                "amount": float(exp.amount),
                "date": exp.date.isoformat(),
                "created_at": exp.created_at.isoformat()
            } for exp in expenses
        ],
        "budgets": [
            {
                "id": str(budget.id),
                "category_id": str(budget.category_id) if budget.category_id else None,
                "amount": float(budget.amount),
                "period": budget.period,
                "start_date": budget.start_date.isoformat(),
                "end_date": budget.end_date.isoformat(),
                "alert_percentage": budget.alert_percentage,
                "created_at": budget.created_at.isoformat()
            } for budget in budgets
        ],
        "export_date": func.now().isoformat(),
        "total_expenses": len(expenses),
        "total_categories": len(categories),
        "total_budgets": len(budgets)
    }
    
    return {
        "message": "Datos exportados exitosamente",
        "data": export_data
    }