from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    preferred_currency: str = Field(default="EUR")
    
    @validator('preferred_currency')
    def validate_currency(cls, v):
        allowed_currencies = ['EUR', 'USD', 'GBP']
        if v not in allowed_currencies:
            raise ValueError(f'Currency must be one of: {allowed_currencies}')
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    preferred_currency: Optional[str] = None
    
    @validator('preferred_currency')
    def validate_currency(cls, v):
        if v is not None:
            allowed_currencies = ['EUR', 'USD', 'GBP']
            if v not in allowed_currencies:
                raise ValueError(f'Currency must be one of: {allowed_currencies}')
        return v


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    """Schema extendido para el perfil con estadísticas"""
    total_expenses: Optional[float] = 0
    total_categories: Optional[int] = 0
    active_budgets: Optional[int] = 0
