from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    icon: str = Field(..., min_length=1)  # Emoji o nombre del icono
    color: str = Field(..., pattern="^#[0-9A-Fa-f]{6}$")  # Código hex válido
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    icon: Optional[str] = Field(None, min_length=1)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryWithStats(CategoryResponse):
    """Schema con estadísticas de gastos"""
    total_expenses: float = 0
    expense_count: int = 0
    budget_amount: Optional[float] = None
    budget_used_percentage: Optional[float] = None