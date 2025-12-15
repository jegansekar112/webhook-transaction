"""
Database models for the webhook service.
Defines the Transaction model to store webhook transaction data.
"""
from sqlalchemy import Column, String, Numeric, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum

# Enum for transaction status
class TransactionStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"  # Transaction is being processed
    PROCESSED = "PROCESSED"    # Transaction has been successfully processed

class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String, primary_key=True, index=True, unique=True)
    
    source_account = Column(String, nullable=False)
    destination_account = Column(String, nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    
    status = Column(SQLEnum(TransactionStatus), nullable=False, default=TransactionStatus.PROCESSING)
    
    created_at = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True) 



