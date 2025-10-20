from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from database import SessionLocal
from models.budget import Budget
from models.user import User
from models.category import Category
from models.transactions import Expense
from schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetResponse, BudgetWithStats, BudgetStatus
)
from routers.auth import get_current_user
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid

router = APIRouter(prefix="/api/budgets", tags=["💰 Presupuestos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_budget_stats(budget: Budget, db: Session) -> dict:
    """Calcular estadísticas de uso del presupuesto"""
    
    # Obtener gastos del período del presupuesto
    expenses_query = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        and_(
            Expense.user_id == budget.user_id,
            Expense.date >= budget.start_date,
            Expense.date <= budget.end_date
        )
    )
    
    # Si tiene categoría específica, filtrar por ella
    if budget.category_id:
        expenses_query = expenses_query.filter(Expense.category_id == budget.category_id)
    
    spent_amount = expenses_query.scalar() or Decimal('0')
    remaining_amount = budget.amount - spent_amount
    used_percentage = (spent_amount / budget.amount * 100) if budget.amount > 0 else 0
    is_exceeded = spent_amount > budget.amount
    
    # Calcular días restantes
    today = date.today()
    days_remaining = (budget.end_date - today).days if budget.end_date > today else 0
    
    return {
        "spent_amount": spent_amount,
        "remaining_amount": remaining_amount,
        "used_percentage": float(used_percentage),
        "is_exceeded": is_exceeded,
        "days_remaining": max(0, days_remaining)
    }

# ========================
# 🔹 Obtener todos los presupuestos activos
# ========================
@router.get("/", response_model=List[BudgetWithStats])
def get_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_expired: bool = False
):
    query = db.query(Budget).filter(Budget.user_id == current_user.id)
    
    # Filtrar por activos si no se incluyen expirados
    if not include_expired:
        today = date.today()
        query = query.filter(Budget.end_date >= today)
    
    budgets = query.order_by(Budget.created_at.desc()).all()
    
    budgets_with_stats = []
    for budget in budgets:
        stats = calculate_budget_stats(budget, db)
        
        # Obtener nombre de categoría si aplica
        category_name = None
        if budget.category_id:
            category = db.query(Category).filter(Category.id == budget.category_id).first()
            category_name = category.name if category else None
        
        budget_with_stats = BudgetWithStats(
            id=budget.id,
            user_id=budget.user_id,
            category_id=budget.category_id,
            amount=budget.amount,
            period=budget.period,
            start_date=budget.start_date,
            end_date=budget.end_date,
            alert_percentage=budget.alert_percentage,
            created_at=budget.created_at,
            category_name=category_name,
            **stats
        )
        budgets_with_stats.append(budget_with_stats)
    
    return budgets_with_stats

# ========================
# 🔹 Crear/actualizar presupuesto
# ========================
@router.post("/", response_model=BudgetResponse)
def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar que la categoría pertenece al usuario si se especifica
    if budget.category_id:
        category = db.query(Category).filter(
            and_(
                Category.id == budget.category_id,
                Category.user_id == current_user.id
            )
        ).first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar si ya existe un presupuesto para la misma categoría en el período
    existing_budget = db.query(Budget).filter(
        and_(
            Budget.user_id == current_user.id,
            Budget.category_id == budget.category_id,
            or_(
                and_(Budget.start_date <= budget.start_date, Budget.end_date >= budget.start_date),
                and_(Budget.start_date <= budget.end_date, Budget.end_date >= budget.end_date),
                and_(Budget.start_date >= budget.start_date, Budget.end_date <= budget.end_date)
            )
        )
    ).first()
    
    if existing_budget:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un presupuesto para esta categoría en el período especificado"
        )
    
    # Crear nuevo presupuesto
    new_budget = Budget(
        user_id=current_user.id,
        category_id=budget.category_id,
        amount=budget.amount,
        period=budget.period,
        start_date=budget.start_date,
        end_date=budget.end_date,
        alert_percentage=budget.alert_percentage
    )
    
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    
    return new_budget

# ========================
# 🔹 Obtener presupuesto específico
# ========================
@router.get("/{budget_id}", response_model=BudgetWithStats)
def get_budget(
    budget_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = db.query(Budget).filter(
        and_(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        )
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    stats = calculate_budget_stats(budget, db)
    
    # Obtener nombre de categoría si aplica
    category_name = None
    if budget.category_id:
        category = db.query(Category).filter(Category.id == budget.category_id).first()
        category_name = category.name if category else None
    
    return BudgetWithStats(
        id=budget.id,
        user_id=budget.user_id,
        category_id=budget.category_id,
        amount=budget.amount,
        period=budget.period,
        start_date=budget.start_date,
        end_date=budget.end_date,
        alert_percentage=budget.alert_percentage,
        created_at=budget.created_at,
        category_name=category_name,
        **stats
    )

# ========================
# 🔹 Actualizar presupuesto
# ========================
@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: uuid.UUID,
    budget_update: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = db.query(Budget).filter(
        and_(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        )
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    # Actualizar campos
    update_data = budget_update.dict(exclude_unset=True)
    
    # Verificar categoría si se está actualizando
    if 'category_id' in update_data and update_data['category_id']:
        category = db.query(Category).filter(
            and_(
                Category.id == update_data['category_id'],
                Category.user_id == current_user.id
            )
        ).first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    for field, value in update_data.items():
        setattr(budget, field, value)
    
    db.commit()
    db.refresh(budget)
    
    return budget

# ========================
# 🔹 Eliminar presupuesto
# ========================
@router.delete("/{budget_id}")
def delete_budget(
    budget_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = db.query(Budget).filter(
        and_(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        )
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    db.delete(budget)
    db.commit()
    
    return {"message": "Presupuesto eliminado exitosamente"}

# ========================
# 🔹 Estado actual de presupuestos
# ========================
@router.get("/status", response_model=BudgetStatus)
def get_budget_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    
    # Obtener presupuestos activos
    active_budgets = db.query(Budget).filter(
        and_(
            Budget.user_id == current_user.id,
            Budget.end_date >= today
        )
    ).all()
    
    total_budgets = len(active_budgets)
    total_budget_amount = sum(budget.amount for budget in active_budgets)
    
    exceeded_count = 0
    total_spent = Decimal('0')
    
    for budget in active_budgets:
        stats = calculate_budget_stats(budget, db)
        total_spent += stats['spent_amount']
        
        if stats['is_exceeded']:
            exceeded_count += 1
    
    overall_percentage = (total_spent / total_budget_amount * 100) if total_budget_amount > 0 else 0
    
    return BudgetStatus(
        total_budgets=total_budgets,
        active_budgets=total_budgets,  # Todos son activos por el filtro
        exceeded_budgets=exceeded_count,
        total_budget_amount=total_budget_amount,
        total_spent=total_spent,
        overall_percentage=float(overall_percentage)
    )

# ========================
# 🔹 Presupuestos por categoría
# ========================
@router.get("/by-category", response_model=List[dict])
def get_budgets_by_category(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    
    # Obtener presupuestos activos con sus categorías
    results = db.query(Budget, Category).outerjoin(
        Category, Budget.category_id == Category.id
    ).filter(
        and_(
            Budget.user_id == current_user.id,
            Budget.end_date >= today
        )
    ).all()
    
    budgets_by_category = []
    for budget, category in results:
        stats = calculate_budget_stats(budget, db)
        
        budget_info = {
            "budget_id": str(budget.id),
            "category_id": str(budget.category_id) if budget.category_id else None,
            "category_name": category.name if category else "General",
            "category_icon": category.icon if category else "💰",
            "category_color": category.color if category else "#6366F1",
            "budget_amount": float(budget.amount),
            "spent_amount": float(stats['spent_amount']),
            "remaining_amount": float(stats['remaining_amount']),
            "used_percentage": stats['used_percentage'],
            "is_exceeded": stats['is_exceeded'],
            "alert_percentage": budget.alert_percentage,
            "days_remaining": stats['days_remaining']
        }
        
        budgets_by_category.append(budget_info)
    
    return budgets_by_category