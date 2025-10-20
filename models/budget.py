from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)  # null = presupuesto general
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    period = Column(String, nullable=False)  # 'monthly', 'weekly', 'yearly'
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    alert_percentage = Column(Integer, default=80)  # 80 = alerta al 80%
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 🔹 Relaciones
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")