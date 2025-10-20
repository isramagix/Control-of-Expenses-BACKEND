from pydantic import BaseModel, Field, validator
from datetime import date as DateType
from decimal import Decimal
from typing import List, Optional, Dict, Any
import uuid

# ========================
# 🔹 Esquemas para Dashboard
# ========================
class DashboardMetrics(BaseModel):
    total_expenses_month: Decimal = Field(description="Total de gastos del mes actual")
    total_expenses_year: Decimal = Field(description="Total de gastos del año actual")
    monthly_budget: Decimal = Field(description="Presupuesto mensual del usuario")
    budget_used_percentage: float = Field(description="Porcentaje de presupuesto usado")
    expenses_count_month: int = Field(description="Número de gastos del mes")
    top_category: Optional[str] = Field(description="Categoría más gastada del mes")
    recent_expenses: List[Dict[str, Any]] = Field(description="Gastos recientes")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ========================
# 🔹 Esquemas para Reportes Mensuales
# ========================
class MonthlyReport(BaseModel):
    year: int = Field(description="Año del reporte")
    month: int = Field(description="Mes del reporte (1-12)")
    total_expenses: Decimal = Field(description="Total de gastos del mes")
    expense_count: int = Field(description="Número total de gastos")
    daily_expenses: Optional[Dict[int, float]] = Field(description="Gastos por día del mes")
    category_breakdown: Optional[Dict[str, float]] = Field(description="Desglose por categorías")
    budget_comparison: Optional[float] = Field(description="Presupuesto mensual para comparación")

    @validator('month')
    def validate_month(cls, v):
        if not 1 <= v <= 12:
            raise ValueError('El mes debe estar entre 1 y 12')
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ========================
# 🔹 Esquemas para Reportes Anuales
# ========================
class YearlyReport(BaseModel):
    year: int = Field(description="Año del reporte")
    total_expenses: Decimal = Field(description="Total de gastos del año")
    expense_count: int = Field(description="Número total de gastos")
    monthly_expenses: Optional[Dict[int, float]] = Field(description="Gastos por mes")
    category_totals: Optional[Dict[str, float]] = Field(description="Totales por categoría")
    average_monthly: Decimal = Field(description="Promedio mensual de gastos")

    @validator('year')
    def validate_year(cls, v):
        if v < 2000 or v > 2100:
            raise ValueError('Año fuera del rango válido')
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ========================
# 🔹 Esquemas para Distribución por Categorías
# ========================
class CategoryDistribution(BaseModel):
    category_id: uuid.UUID = Field(description="ID de la categoría")
    category_name: str = Field(description="Nombre de la categoría")
    category_color: Optional[str] = Field(description="Color de la categoría")
    category_icon: Optional[str] = Field(description="Icono de la categoría")
    total_amount: Decimal = Field(description="Monto total gastado en la categoría")
    expense_count: int = Field(description="Número de gastos en la categoría")
    percentage: float = Field(description="Porcentaje del total de gastos")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ========================
# 🔹 Esquemas para Tendencias
# ========================
class SpendingTrend(BaseModel):
    date: DateType = Field(description="Fecha del gasto")
    amount: Decimal = Field(description="Monto total del día")
    moving_average: Optional[Decimal] = Field(None, description="Media móvil de 7 días")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ========================
# 🔹 Esquemas para Top Gastos
# ========================
class TopExpense(BaseModel):
    id: uuid.UUID = Field(description="ID del gasto")
    description: str = Field(description="Descripción del gasto")
    amount: Decimal = Field(description="Monto del gasto")
    date: DateType = Field(description="Fecha del gasto")
    category_name: str = Field(description="Nombre de la categoría")
    category_icon: Optional[str] = Field(description="Icono de la categoría")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ========================
# 🔹 Esquemas para Progreso Semanal
# ========================
class WeeklyProgress(BaseModel):
    week_start: DateType = Field(description="Inicio de la semana (lunes)")
    week_end: DateType = Field(description="Fin de la semana (domingo)")
    total_expenses: Decimal = Field(description="Total de gastos de la semana")
    daily_breakdown: Dict[str, float] = Field(description="Gastos por día de la semana")
    budget_percentage: Optional[float] = Field(description="Porcentaje del presupuesto semanal usado")
    comparison_last_week: Decimal = Field(description="Gastos de la semana anterior para comparación")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ========================
# 🔹 Filtros para Reportes (Opcional)
# ========================
class ReportsFilters(BaseModel):
    start_date: Optional[DateType] = Field(None, description="Fecha de inicio del filtro")
    end_date: Optional[DateType] = Field(None, description="Fecha de fin del filtro")
    category_ids: Optional[List[uuid.UUID]] = Field(None, description="IDs de categorías a filtrar")
    min_amount: Optional[Decimal] = Field(None, description="Monto mínimo")
    max_amount: Optional[Decimal] = Field(None, description="Monto máximo")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v

    class Config:
        from_attributes = True