from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from database import SessionLocal
from models.user import User
from models.category import Category
from models.transactions import Expense
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithStats
from routers.auth import get_current_user
from typing import List, Optional
import uuid

router = APIRouter(prefix="/api/categories", tags=["Categories"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================
# 🔹 Obtener todas las categorías (usuario + sistema)
# ========================
@router.get("/", response_model=List[CategoryWithStats])
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_stats: bool = False
):
    # Obtener categorías del usuario + categorías del sistema
    categories = db.query(Category).filter(
        and_(
            Category.user_id == current_user.id,
            Category.is_system == False
        )
    ).all()
    
    # TODO: Agregar categorías del sistema cuando las implementemos
    
    if not include_stats:
        return [CategoryWithStats(**category.__dict__) for category in categories]
    
    # Calcular estadísticas para cada categoría
    categories_with_stats = []
    for category in categories:
        # Calcular gastos totales de la categoría
        expense_stats = db.query(
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id)
        ).filter(Expense.category_id == category.id).first()
        
        total_expenses = float(expense_stats[0] or 0)
        expense_count = expense_stats[1] or 0
        
        category_with_stats = CategoryWithStats(
            id=category.id,
            user_id=category.user_id,
            name=category.name,
            icon=category.icon,
            color=category.color,
            is_system=category.is_system,
            created_at=category.created_at,
            total_expenses=total_expenses,
            expense_count=expense_count
        )
        
        categories_with_stats.append(category_with_stats)
    
    return categories_with_stats

# ========================
# 🔹 Crear nueva categoría
# ========================
@router.post("/", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar que el usuario no tenga ya una categoría con el mismo nombre
    existing_category = db.query(Category).filter(
        and_(
            Category.user_id == current_user.id,
            Category.name.ilike(category.name.strip())
        )
    ).first()
    
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Ya tienes una categoría con ese nombre"
        )
    
    # Crear nueva categoría
    new_category = Category(
        user_id=current_user.id,
        name=category.name.strip(),
        icon=category.icon,
        color=category.color,
        is_system=False
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category

# ========================
# 🔹 Obtener categoría específica
# ========================
@router.get("/{category_id}", response_model=CategoryWithStats)
def get_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        and_(
            Category.id == category_id,
            Category.user_id == current_user.id
        )
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Calcular estadísticas
    expense_stats = db.query(
        func.coalesce(func.sum(Expense.amount), 0),
        func.count(Expense.id)
    ).filter(Expense.category_id == category.id).first()
    
    total_expenses = float(expense_stats[0] or 0)
    expense_count = expense_stats[1] or 0
    
    return CategoryWithStats(
        id=category.id,
        user_id=category.user_id,
        name=category.name,
        icon=category.icon,
        color=category.color,
        is_system=category.is_system,
        created_at=category.created_at,
        total_expenses=total_expenses,
        expense_count=expense_count
    )

# ========================
# 🔹 Actualizar categoría
# ========================
@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        and_(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.is_system == False  # No permitir editar categorías del sistema
        )
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar nombre único si se está actualizando
    update_data = category_update.dict(exclude_unset=True)
    if 'name' in update_data:
        existing_category = db.query(Category).filter(
            and_(
                Category.user_id == current_user.id,
                Category.name.ilike(update_data['name'].strip()),
                Category.id != category_id
            )
        ).first()
        
        if existing_category:
            raise HTTPException(
                status_code=400,
                detail="Ya tienes una categoría con ese nombre"
            )
    
    # Actualizar campos
    for field, value in update_data.items():
        if field == 'name' and value:
            setattr(category, field, value.strip())
        else:
            setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    return category

# ========================
# 🔹 Eliminar categoría
# ========================
@router.delete("/{category_id}")
def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    force: bool = False
):
    category = db.query(Category).filter(
        and_(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.is_system == False  # No permitir eliminar categorías del sistema
        )
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar si tiene gastos asociados
    expense_count = db.query(Expense).filter(Expense.category_id == category_id).count()
    
    if expense_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la categoría. Tiene {expense_count} gastos asociados. Usa force=true para eliminar de todas formas."
        )
    
    # Eliminar la categoría (cascade eliminará gastos si force=true)
    db.delete(category)
    db.commit()
    
    return {"message": "Categoría eliminada exitosamente"}

# ========================
# 🔹 Obtener categorías más utilizadas
# ========================
@router.get("/stats/most-used")
def get_most_used_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 5
):
    # Obtener categorías con más gastos
    most_used = db.query(
        Category,
        func.count(Expense.id).label('expense_count'),
        func.coalesce(func.sum(Expense.amount), 0).label('total_amount')
    ).join(
        Expense, Category.id == Expense.category_id
    ).filter(
        Category.user_id == current_user.id
    ).group_by(
        Category.id
    ).order_by(
        func.count(Expense.id).desc()
    ).limit(limit).all()
    
    return [
        {
            "category": {
                "id": str(result[0].id),
                "name": result[0].name,
                "icon": result[0].icon,
                "color": result[0].color
            },
            "expense_count": result[1],
            "total_amount": float(result[2])
        }
        for result in most_used
    ]