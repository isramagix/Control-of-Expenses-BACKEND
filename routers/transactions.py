from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from database import SessionLocal
from models.transactions import Expense
from models.user import User
from models.category import Category
from schemas.transactions import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseWithCategory,
    ExpenseFilters, ExpenseSummary
)
from routers.auth import get_current_user
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid
import calendar

router = APIRouter(prefix="/api/expenses", tags=["💸 Gastos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================
# 🔹 Obtener gastos con filtros avanzados
# ========================
@router.get("/", response_model=List[ExpenseWithCategory])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category_id: Optional[uuid.UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None
):
    # Construir query base
    query = db.query(Expense, Category).join(
        Category, Expense.category_id == Category.id
    ).filter(Expense.user_id == current_user.id)
    
    # Aplicar filtros
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    
    if start_date:
        query = query.filter(Expense.date >= start_date)
    
    if end_date:
        query = query.filter(Expense.date <= end_date)
    
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Expense.description.ilike(search_term),
                Category.name.ilike(search_term)
            )
        )
    
    # Ordenar por fecha descendente
    query = query.order_by(desc(Expense.date), desc(Expense.created_at))
    
    # Paginación
    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()
    
    # Formatear respuesta
    expenses_with_category = []
    for expense, category in results:
        expense_with_cat = ExpenseWithCategory(
            id=expense.id,
            user_id=expense.user_id,
            category_id=expense.category_id,
            description=expense.description,
            amount=expense.amount,
            date=expense.date,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
            category_name=category.name,
            category_icon=category.icon,
            category_color=category.color
        )
        expenses_with_category.append(expense_with_cat)
    
    return expenses_with_category

# ========================
# 🔹 Crear nuevo gasto
# ========================
@router.post("/", response_model=ExpenseResponse)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar que la categoría pertenece al usuario
    category = db.query(Category).filter(
        and_(
            Category.id == expense.category_id,
            Category.user_id == current_user.id
        )
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Categoría no encontrada"
        )
    
    # Crear nuevo gasto
    new_expense = Expense(
        user_id=current_user.id,
        category_id=expense.category_id,
        description=expense.description,
        amount=expense.amount,
        date=expense.date
    )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    return new_expense

# ========================
# 🔹 Obtener gasto específico
# ========================
@router.get("/{expense_id}", response_model=ExpenseWithCategory)
def get_expense(
    expense_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = db.query(Expense, Category).join(
        Category, Expense.category_id == Category.id
    ).filter(
        and_(
            Expense.id == expense_id,
            Expense.user_id == current_user.id
        )
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    expense, category = result
    
    return ExpenseWithCategory(
        id=expense.id,
        user_id=expense.user_id,
        category_id=expense.category_id,
        description=expense.description,
        amount=expense.amount,
        date=expense.date,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
        category_name=category.name,
        category_icon=category.icon,
        category_color=category.color
    )

# ========================
# 🔹 Actualizar gasto
# ========================
@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: uuid.UUID,
    expense_update: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        and_(
            Expense.id == expense_id,
            Expense.user_id == current_user.id
        )
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    # Verificar categoría si se está actualizando
    update_data = expense_update.dict(exclude_unset=True)
    if 'category_id' in update_data:
        category = db.query(Category).filter(
            and_(
                Category.id == update_data['category_id'],
                Category.user_id == current_user.id
            )
        ).first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Actualizar campos
    for field, value in update_data.items():
        setattr(expense, field, value)
    
    db.commit()
    db.refresh(expense)
    
    return expense

# ========================
# 🔹 Eliminar gasto
# ========================
@router.delete("/{expense_id}")
def delete_expense(
    expense_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        and_(
            Expense.id == expense_id,
            Expense.user_id == current_user.id
        )
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    db.delete(expense)
    db.commit()
    
    return {"message": "Gasto eliminado exitosamente"}

# ========================
# 🔹 Obtener gastos recientes
# ========================
@router.get("/recent", response_model=List[ExpenseWithCategory])
def get_recent_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
):
    results = db.query(Expense, Category).join(
        Category, Expense.category_id == Category.id
    ).filter(
        Expense.user_id == current_user.id
    ).order_by(
        desc(Expense.created_at)
    ).limit(limit).all()
    
    return [
        ExpenseWithCategory(
            id=expense.id,
            user_id=expense.user_id,
            category_id=expense.category_id,
            description=expense.description,
            amount=expense.amount,
            date=expense.date,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
            category_name=category.name,
            category_icon=category.icon,
            category_color=category.color
        )
        for expense, category in results
    ]

# ========================
# 🔹 Resumen de gastos del mes actual
# ========================
@router.get("/summary", response_model=ExpenseSummary)
def get_expense_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    year: Optional[int] = None,
    month: Optional[int] = None
):
    # Usar mes actual si no se especifica
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    # Calcular fechas del período
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    # Obtener gastos del período
    expenses = db.query(Expense).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
    ).all()
    
    if not expenses:
        return ExpenseSummary(
            total_amount=Decimal('0'),
            expense_count=0,
            average_expense=Decimal('0'),
            period_start=start_date,
            period_end=end_date
        )
    
    # Calcular estadísticas
    total_amount = sum(exp.amount for exp in expenses)
    expense_count = len(expenses)
    average_expense = total_amount / expense_count if expense_count > 0 else Decimal('0')
    
    # Encontrar categoría más gastada
    category_totals = {}
    for expense in expenses:
        if expense.category_id not in category_totals:
            category_totals[expense.category_id] = Decimal('0')
        category_totals[expense.category_id] += expense.amount
    
    top_category = None
    if category_totals:
        top_category_id = max(category_totals, key=category_totals.get)
        top_category_obj = db.query(Category).filter(Category.id == top_category_id).first()
        top_category = top_category_obj.name if top_category_obj else None
    
    return ExpenseSummary(
        total_amount=total_amount,
        expense_count=expense_count,
        average_expense=average_expense,
        period_start=start_date,
        period_end=end_date,
        top_category=top_category
    )
