from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    monthly_budget = Column(Numeric(precision=10, scale=2), default=0)
    renewal_day = Column(Integer, default=1)  # 1, 15, 30
    budget_alert_percentage = Column(Integer, default=80)
    notifications = Column(JSON, default={
        "budget_reminders": True,
        "excessive_spending_alerts": True,
        "monthly_email_summary": False,
        "push_notifications": True
    })
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 🔹 Relación
    user = relationship("User", back_populates="settings")