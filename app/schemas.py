"""
Pydantic schemas for request/response validation.
These schemas define the structure of API requests and responses.
"""
from pydantic import BaseModel, Field, field_validator, field_serializer
from datetime import datetime
from typing import Optional
from app.models import TransactionStatus

# Schema for incoming webhook request validation
class WebhookRequest(BaseModel):
    """
    Validates incoming webhook request data
    """
    transaction_id: str = Field(..., min_length=1, description="Unique transaction identifier")
    source_account: str = Field(..., min_length=1, description="Source account identifier")
    destination_account: str = Field(..., min_length=1, description="Destination account identifier")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code (3 letters)")
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code is exactly 3 uppercase letters"""
        if len(v) != 3:
            raise ValueError('Currency must be exactly 3 characters')
        return v.upper()

# Schema for transaction response serialization
class TransactionResponse(BaseModel):
    """
    Serializes transaction data for API responses 
    """
    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str
    status: TransactionStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    # Serialize datetime fields to required format: "2024-01-15T10:30:00Z"
    @field_serializer('created_at', 'processed_at')
    def serialize_datetime(self, value: Optional[datetime], _info) -> Optional[str]:
        """Serialize datetime to ISO format with Z suffix"""
        if value is None:
            return None
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    model_config = {
        "from_attributes": True  
    }