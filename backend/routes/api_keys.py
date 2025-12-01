from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, status
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from models.user_models import (
    APIKeyCreate, 
    APIKeyResponse, 
    APIKeyListResponse,
    APIKeyUpdate,
    SuccessResponse,
    ErrorResponse
)
from models.database_models import UserAPIKeyDB
from security.encryption import encryption_service
from security.rate_limiter import check_rate_limit
from routes.auth import validate_user_session
from database.supabase_client import supabase_manager


router = APIRouter(prefix="/api/user/keys", tags=["api-keys"])


@router.get("/", response_model=APIKeyListResponse)
async def list_api_keys(
    request: Request,
    current_user: dict = Depends(validate_user_session)
) -> APIKeyListResponse:
    """Get all API keys for the current user"""
    try:
        await check_rate_limit(request, current_user["user_id"])
        
        # Log the action
        await supabase_manager.log_security_audit(
            user_id=current_user["user_id"],
            action="list_api_keys",
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
        
        keys_data = await supabase_manager.get_user_api_keys(current_user["user_id"])
        
        keys = [
            APIKeyResponse(
                id=key["id"],
                service_name=key["service_name"],
                key_version=key["key_version"],
                created_at=key["created_at"],
                updated_at=key["updated_at"]
            )
            for key in keys_data
        ]
        
        return APIKeyListResponse(keys=keys, total_count=len(keys))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API keys: {str(e)}"
        )


@router.post("/", response_model=APIKeyResponse)
async def create_or_update_api_key(
    request: Request,
    key_data: APIKeyCreate,
    current_user: dict = Depends(validate_user_session)
) -> APIKeyResponse:
    """Create or update an API key for a service"""
    try:
        await check_rate_limit(request, current_user["user_id"])
        
        # Encrypt the API key before storage
        encrypted_key = encryption_service.encrypt_api_key(key_data.api_key)
        
        # Store in database
        db_key = await supabase_manager.upsert_api_key(
            user_id=current_user["user_id"],
            service_name=key_data.service_name,
            encrypted_key=encrypted_key,
            key_version=1
        )
        
        if not db_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save API key"
            )
        
        # Log the action
        await supabase_manager.log_security_audit(
            user_id=current_user["user_id"],
            action="upsert_api_key",
            service_name=key_data.service_name,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
        
        return APIKeyResponse(
            id=db_key["id"],
            service_name=db_key["service_name"],
            key_version=db_key["key_version"],
            created_at=db_key["created_at"],
            updated_at=db_key["updated_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save API key: {str(e)}"
        )


@router.delete("/{service_name}", response_model=SuccessResponse)
async def delete_api_key(
    request: Request,
    service_name: str,
    current_user: dict = Depends(validate_user_session)
) -> SuccessResponse:
    """Delete an API key for a specific service"""
    try:
        await check_rate_limit(request, current_user["user_id"])
        
        # Verify the key exists
        existing_key = await supabase_manager.get_api_key(current_user["user_id"], service_name)
        if not existing_key:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"No API key found for service: {service_name}"
            )
        
        # Delete the key
        success = await supabase_manager.delete_api_key(current_user["user_id"], service_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete API key"
            )
        
        # Log the action
        await supabase_manager.log_security_audit(
            user_id=current_user["user_id"],
            action="delete_api_key",
            service_name=service_name,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
        
        return SuccessResponse(
            message="API key deleted successfully",
            service_name=service_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}"
        )


@router.post("/rotate", response_model=SuccessResponse)
async def rotate_encryption_keys(
    request: Request,
    current_user: dict = Depends(validate_user_session)
) -> SuccessResponse:
    """Rotate encryption keys for all user API keys"""
    try:
        await check_rate_limit(request, current_user["user_id"])
        
        # Get all user keys
        keys_data = await supabase_manager.get_user_api_keys(current_user["user_id"])
        
        if not keys_data:
            return SuccessResponse(
                message="No API keys to rotate",
                service_name="all"
            )
        
        #