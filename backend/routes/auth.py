from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
import jwt
from datetime import datetime

from config import settings


security = HTTPBearer()


class JWTValidator:
    def __init__(self):
        self.secret_key = settings.jwt_secret
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


jwt_validator = JWTValidator()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency to get current user from JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    token = credentials.credentials
    payload = jwt_validator.validate_token(token)
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return {"user_id": user_id, "email": payload.get("email"), "role": payload.get("role")}


async def validate_user_session(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Enhanced session validation with additional security checks"""
    # Check if user is active (you might want to add more checks here)
    if not current_user.get("user_id"):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="User session invalid"
        )
    
    # Log session validation for audit
    # In a real implementation, you'd log this to your audit system
    
    return current_user