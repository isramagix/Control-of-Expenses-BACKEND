from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


class NotificationSettings(BaseModel):
    budget_reminders: bool = True
    excessive_spending_alerts: bool = True
    monthly_email_summary: bool = False
    push_notifications: bool = True


class UserSettingsBase(BaseModel):
    monthly_budget: Decimal = Field(default=0, ge=0, decimal_places=2)
    renewal_day: int = Field(default=1, ge=1, le=31)
    budget_alert_percentage: int = Field(default=80, ge=1, le=100)
    notifications: NotificationSettings = NotificationSettings()


class UserSettingsUpdate(BaseModel):
    monthly_budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    renewal_day: Optional[int] = Field(None, ge=1, le=31)
    budget_alert_percentage: Optional[int] = Field(None, ge=1, le=100)
    notifications: Optional[NotificationSettings] = None


class UserSettingsResponse(UserSettingsBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SettingsWithStats(UserSettingsResponse):
    """Settings con estadísticas adicionales"""
    current_month_spent: Decimal = 0
    budget_used_percentage: float = 0
    days_until_renewal: int = 0
    monthly_average_spending: Decimal = 0