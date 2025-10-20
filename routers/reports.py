from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, desc
from database import SessionLocal
from models.transactions import Expense
from models.user import User
from models.category import Category
from models.budget import Budget
from schemas.reports import (
    DashboardMetrics, MonthlyReport, YearlyReport, CategoryDistribution,
    SpendingTrend, TopExpense, WeeklyProgress, ReportsFilters
)
from routers.auth import get_current_user
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import calendar

router = APIRouter(prefix="/api/reports", tags=["Reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================
# 🔹 Dashboard principal
# ========================
@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now()
    current_month_start = date(now.year, now.month, 1)
    current_year_start = date(now.year, 1, 1)
    
    # Gastos del mes actual
    monthly_expenses = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= current_month_start
        )
    ).scalar() or Decimal('0')
    
    # Gastos del año actual
    yearly_expenses = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= current_year_start
        )
    ).scalar() or Decimal('0')
    
    # Presupuesto mensual (de configuraciones de usuario)
    monthly_budget = Decimal('0')
    if current_user.settings:
        monthly_budget = current_user.settings.monthly_budget
    
    # Porcentaje de presupuesto usado
    budget_percentage = (monthly_expenses / monthly_budget * 100) if monthly_budget > 0 else 0
    
    # Contar gastos del mes
    monthly_expense_count = db.query(Expense).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= current_month_start
        )
    ).count()
    
    # Categoría más gastada del mes
    top_category_result = db.query(
        Category.name,
        func.sum(Expense.amount).label('total')
    ).join(
        Expense, Category.id == Expense.category_id
    ).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= current_month_start
        )
    ).group_by(Category.name).order_by(desc('total')).first()
    
    top_category = top_category_result[0] if top_category_result else None
    
    # Gastos recientes
    recent_expenses_query = db.query(Expense, Category).join(
        Category, Expense.category_id == Category.id
    ).filter(
        Expense.user_id == current_user.id
    ).order_by(desc(Expense.created_at)).limit(5)
    
    recent_expenses = []
    for expense, category in recent_expenses_query:
        recent_expenses.append({
            "id": str(expense.id),
            "description": expense.description,
            "amount": float(expense.amount),
            "date": expense.date.isoformat(),
            "category_name": category.name,
            "category_icon": category.icon,
            "category_color": category.color
        })
    
    return DashboardMetrics(
        total_expenses_month=monthly_expenses,
        total_expenses_year=yearly_expenses,
        monthly_budget=monthly_budget,
        budget_used_percentage=float(budget_percentage),
        expenses_count_month=monthly_expense_count,
        top_category=top_category,
        recent_expenses=recent_expenses
    )

# ========================
# 🔹 Reporte mensual
# ========================
@router.get("/monthly/{year}/{month}", response_model=MonthlyReport)
def get_monthly_report(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validar mes y año
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Mes inválido")
    
    # Calcular fechas del período
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    # Obtener gastos del mes
    expenses = db.query(Expense, Category).join(
        Category, Expense.category_id == Category.id
    ).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
    ).all()
    
    if not expenses:
        return MonthlyReport(
            year=year,
            month=month,
            total_expenses=Decimal('0'),
            expense_count=0
        )
    
    # Calcular totales
    total_expenses = sum(expense.amount for expense, _ in expenses)
    expense_count = len(expenses)
    
    # Gastos por día
    daily_expenses = {}
    for expense, _ in expenses:
        day = expense.date.day
        if day not in daily_expenses:
            daily_expenses[day] = Decimal('0')
        daily_expenses[day] += expense.amount
    
    # Convertir a float para JSON
    daily_expenses = {k: float(v) for k, v in daily_expenses.items()}
    
    # Gastos por categoría
    category_breakdown = {}
    for expense, category in expenses:
        if category.name not in category_breakdown:
            category_breakdown[category.name] = Decimal('0')
        category_breakdown[category.name] += expense.amount
    
    # Convertir a float para JSON
    category_breakdown = {k: float(v) for k, v in category_breakdown.items()}
    
    # Comparación con presupuesto
    budget_comparison = None
    if current_user.settings and current_user.settings.monthly_budget > 0:
        budget_comparison = float(current_user.settings.monthly_budget)
    
    return MonthlyReport(
        year=year,
        month=month,
        total_expenses=total_expenses,
        expense_count=expense_count,
        daily_expenses=daily_expenses,
        category_breakdown=category_breakdown,
        budget_comparison=budget_comparison
    )

# ========================
# 🔹 Reporte anual
# ========================
@router.get("/yearly/{year}", response_model=YearlyReport)
def get_yearly_report(
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # Obtener gastos del año
    expenses = db.query(Expense, Category).join(
        Category, Expense.category_id == Category.id
    ).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
    ).all()
    
    if not expenses:
        return YearlyReport(
            year=year,
            total_expenses=Decimal('0'),
            expense_count=0,
            average_monthly=Decimal('0')
        )
    
    total_expenses = sum(expense.amount for expense, _ in expenses)
    expense_count = len(expenses)
    average_monthly = total_expenses / 12
    
    # Gastos por mes
    monthly_expenses = {}
    for expense, _ in expenses:
        month = expense.date.month
        if month not in monthly_expenses:
            monthly_expenses[month] = Decimal('0')
        monthly_expenses[month] += expense.amount
    
    # Convertir a float para JSON
    monthly_expenses = {k: float(v) for k, v in monthly_expenses.items()}
    
    # Totales por categoría
    category_totals = {}
    for expense, category in expenses:
        if category.name not in category_totals:
            category_totals[category.name] = Decimal('0')
        category_totals[category.name] += expense.amount
    
    # Convertir a float para JSON
    category_totals = {k: float(v) for k, v in category_totals.items()}
    
    return YearlyReport(
        year=year,
        total_expenses=total_expenses,
        expense_count=expense_count,
        monthly_expenses=monthly_expenses,
        category_totals=category_totals,
        average_monthly=average_monthly
    )

# ========================
# 🔹 Distribución por categorías
# ========================
@router.get("/category-distribution", response_model=List[CategoryDistribution])
def get_category_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    # Usar último mes por defecto
    if not start_date or not end_date:
        now = datetime.now()
        start_date = date(now.year, now.month, 1)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end_date = date(now.year, now.month, last_day)
    
    # Obtener gastos agrupados por categoría
    results = db.query(
        Category.id,
        Category.name,
        Category.color,
        Category.icon,
        func.coalesce(func.sum(Expense.amount), 0).label('total_amount'),
        func.count(Expense.id).label('expense_count')
    ).outerjoin(
        Expense, and_(
            Category.id == Expense.category_id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
    ).filter(
        Category.user_id == current_user.id
    ).group_by(
        Category.id, Category.name, Category.color, Category.icon
    ).order_by(desc('total_amount')).all()
    
    # Calcular total para porcentajes
    total_all_categories = sum(result.total_amount for result in results)
    
    distribution = []
    for result in results:
        if result.total_amount > 0:  # Solo incluir categorías con gastos
            percentage = (result.total_amount / total_all_categories * 100) if total_all_categories > 0 else 0
            
            distribution.append(CategoryDistribution(
                category_id=result.id,
                category_name=result.name,
                category_color=result.color,
                category_icon=result.icon,
                total_amount=result.total_amount,
                expense_count=result.expense_count,
                percentage=percentage
            ))
    
    return distribution

# ========================
# 🔹 Tendencias de gasto
# ========================
@router.get("/trends", response_model=List[SpendingTrend])
def get_spending_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=7, le=365)
):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Obtener gastos diarios
    daily_totals = db.query(
        Expense.date,
        func.sum(Expense.amount).label('daily_total')
    ).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
    ).group_by(Expense.date).order_by(Expense.date).all()
    
    # Crear lista completa de días (rellenar días sin gastos con 0)
    trends = []
    current_date = start_date
    daily_dict = {result.date: result.daily_total for result in daily_totals}
    
    while current_date <= end_date:
        amount = daily_dict.get(current_date, Decimal('0'))
        trends.append(SpendingTrend(
            date=current_date,
            amount=amount
        ))
        current_date += timedelta(days=1)
    
    # Calcular media móvil de 7 días
    for i in range(len(trends)):
        if i >= 6:  # Necesitamos al menos 7 días para la media
            moving_sum = sum(trend.amount for trend in trends[i-6:i+1])
            trends[i].moving_average = moving_sum / 7
    
    return trends

# ========================
# 🔹 Top gastos del período
# ========================
@router.get("/top-expenses", response_model=List[TopExpense])
def get_top_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    # Usar último mes por defecto
    if not start_date or not end_date:
        now = datetime.now()
        start_date = date(now.year, now.month, 1)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end_date = date(now.year, now.month, last_day)
    
    results = db.query(Expense, Category).join(
        Category, Expense.category_id == Category.id
    ).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
    ).order_by(desc(Expense.amount)).limit(limit).all()
    
    top_expenses = []
    for expense, category in results:
        top_expenses.append(TopExpense(
            id=expense.id,
            description=expense.description,
            amount=expense.amount,
            date=expense.date,
            category_name=category.name,
            category_icon=category.icon
        ))
    
    return top_expenses

# ========================
# 🔹 Progreso semanal
# ========================
@router.get("/weekly-progress", response_model=WeeklyProgress)
def get_weekly_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Calcular semana actual (lunes a domingo)
    today = date.today()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    # Obtener gastos de la semana
    expenses = db.query(Expense).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= week_start,
            Expense.date <= week_end
        )
    ).all()
    
    total_expenses = sum(expense.amount for expense in expenses)
    
    # Gastos por día de la semana
    daily_breakdown = {}
    day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    for i, day_name in enumerate(day_names):
        day_date = week_start + timedelta(days=i)
        day_expenses = sum(expense.amount for expense in expenses if expense.date == day_date)
        daily_breakdown[day_name] = float(day_expenses)
    
    # Comparación con presupuesto semanal (1/4 del mensual)
    budget_percentage = None
    if current_user.settings and current_user.settings.monthly_budget > 0:
        weekly_budget = current_user.settings.monthly_budget / 4
        budget_percentage = (total_expenses / weekly_budget * 100) if weekly_budget > 0 else 0
    
    # Comparación con semana anterior
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_end - timedelta(days=7)
    
    last_week_expenses = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        and_(
            Expense.user_id == current_user.id,
            Expense.date >= last_week_start,
            Expense.date <= last_week_end
        )
    ).scalar() or Decimal('0')
    
    return WeeklyProgress(
        week_start=week_start,
        week_end=week_end,
        total_expenses=total_expenses,  
        daily_breakdown=daily_breakdown,
        budget_percentage=budget_percentage,
        comparison_last_week=last_week_expenses
    )