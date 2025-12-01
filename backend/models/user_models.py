from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class APIKeyCreate(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=50, description="Name of the API service")
    api_key: str = Field(..., min_length=1, description="The API key to encrypt and store")
    
    @validator('service_name')
    def validate_service_name(cls, v):
        allowed_services = ['openai', 'anthropic', 'google', 'azure', 'custom']
        if v.lower() not in allowed_services:
            raise ValueError(f"Service must be one of: {', '.join(allowed_services)}")
        return v.lower()


class APIKeyResponse(BaseModel):
    id: str
    service_name: str
    key_version: int
    created_at: datetime
    updated_at: datetime
    # Note: We don't return the actual API key for security


class APIKeyListResponse(BaseModel):
    keys: List[APIKeyResponse]
    total_count: int


class APIKeyUpdate(BaseModel):
    api_key: str = Field(..., min_length=1, description="The new API key to encrypt and store")


class ErrorResponse(BaseModel):
    error: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    message: str
    service_name: str


class SecurityAuditEntry(BaseModel):
    id: str
    action: str
    service_name: Optional[str] = None
    timestamp: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None