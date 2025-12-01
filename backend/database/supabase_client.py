import os
from supabase import create_client, Client
from typing import Optional, List, Dict, Any

from config import settings


class SupabaseManager:
    def __init__(self):
        self.client: Client = create_client(settings.supabase_url, settings.supabase_key)
    
    async def get_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all API keys for a user"""
        try:
            response = (self.client
                       .table("user_api_keys")
                       .select("*")
                       .eq("user_id", user_id)
                       .execute())
            return response.data
        except Exception as e:
            raise Exception(f"Failed to fetch user API keys: {str(e)}")
    
    async def get_api_key(self, user_id: str, service_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific API key for a user"""
        try:
            response = (self.client
                       .table("user_api_keys")
                       .select("*")
                       .eq("user_id", user_id)
                       .eq("service_name", service_name)
                       .execute())
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to fetch API key: {str(e)}")
    
    async def upsert_api_key(self, user_id: str, service_name: str, encrypted_key: str, key_version: int = 1) -> Dict[str, Any]:
        """Insert or update an API key"""
        try:
            data = {
                "user_id": user_id,
                "service_name": service_name,
                "encrypted_key": encrypted_key,
                "key_version": key_version
            }
            
            response = (self.client
                       .table("user_api_keys")
                       .upsert(data, on_conflict="user_id,service_name")
                       .execute())
            
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Failed to upsert API key: {str(e)}")
    
    async def delete_api_key(self, user_id: str, service_name: str) -> bool:
        """Delete an API key"""
        try:
            response = (self.client
                       .table("user_api_keys")
                       .delete()
                       .eq("user_id", user_id)
                       .eq("service_name", service_name)
                       .execute())
            
            return len(response.data) > 0
        except Exception as e:
            raise Exception(f"Failed to delete API key: {str(e)}")
    
    async def log_security_audit(self, user_id: str, action: str, service_name: Optional[str] = None, 
                               user_agent: Optional[str] = None, ip_address: Optional[str] = None) -> None:
        """Log security audit entry"""
        try:
            data = {
                "user_id": user_id,
                "action": action,
                "service_name": service_name,
                "user_agent": user_agent,
                "ip_address": ip_address
            }
            
            (self.client
             .table("security_audit")
             .insert(data)
             .execute())
        except Exception as e:
            # Don't raise exception for audit failures to avoid breaking main functionality
            print(f"Failed to log security audit: {str(e)}")


# Global Supabase manager instance
supabase_manager = SupabaseManager()