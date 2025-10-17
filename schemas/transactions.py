from pydantic import BaseModel
from datetime import datetime

class TransactionBase(BaseModel):
    type: str
    description: str
    amount: float

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    date: datetime

    class Config:
        from_attributes = True
