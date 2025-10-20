from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from datetime import date as DateType
from decimal import Decimal
import uuid


class ExpenseBase(BaseModel):
    category_id: uuid.UUID
    description: str = Field(..., min_length=1, max_length=200)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    date: DateType
    
    @validator('description')
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    description: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    date: Optional[DateType] = None
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip() if v else v


class ExpenseResponse(ExpenseBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseWithCategory(ExpenseResponse):
    """Schema con información de la categoría"""
    category_name: str
    category_icon: str
    category_color: str


class ExpenseFilters(BaseModel):
    """Schema para filtros de búsqueda"""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    category_id: Optional[uuid.UUID] = None
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    search: Optional[str] = Field(None, max_length=100)
    
    @validator('search')
    def validate_search(cls, v):
        return v.strip() if v else v


class ExpenseSummary(BaseModel):
    """Resumen de gastos del período"""
    total_amount: Decimal
    expense_count: int
    average_expense: Decimal
    period_start: DateType
    period_end: DateType
    top_category: Optional[str] = None
