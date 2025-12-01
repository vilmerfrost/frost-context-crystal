from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class UserAPIKeyDB(BaseModel):
    id: str
    user_id: str
    service_name: str
    encrypted_key: str
    key_version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SecurityAuditDB(BaseModel):
    id: str
    user_id: str
    action: str
    service_name: Optional[str] = None
    timestamp: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    
    class Config:
        from_attributes = True