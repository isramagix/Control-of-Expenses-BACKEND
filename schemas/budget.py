from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from datetime import date as DateType
from decimal import Decimal
import uuid


class BudgetBase(BaseModel):
    category_id: Optional[uuid.UUID] = None  # null = presupuesto general
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    period: str = Field(..., pattern="^(monthly|weekly|yearly)$")
    start_date: DateType
    end_date: DateType
    alert_percentage: int = Field(default=80, ge=1, le=100)
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    period: Optional[str] = Field(None, pattern="^(monthly|weekly|yearly)$")
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    alert_percentage: Optional[int] = Field(None, ge=1, le=100)


class BudgetResponse(BudgetBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetWithStats(BudgetResponse):
    """Schema con estadísticas de uso del presupuesto"""
    category_name: Optional[str] = None
    spent_amount: Decimal = 0
    remaining_amount: Decimal = 0
    used_percentage: float = 0
    is_exceeded: bool = False
    days_remaining: int = 0


class BudgetStatus(BaseModel):
    """Estado general de presupuestos"""
    total_budgets: int
    active_budgets: int
    exceeded_budgets: int
    total_budget_amount: Decimal
    total_spent: Decimal
    overall_percentage: float