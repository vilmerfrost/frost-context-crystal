import time
from typing import Dict, Tuple
from fastapi import HTTPException, Request
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    def is_rate_limited(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit"""
        now = time.time()
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Remove requests older than 1 minute
        self.requests[user_id] = [req_time for req_time in self.requests[user_id] 
                                if now - req_time < 60]
        
        # Check if limit exceeded
        if len(self.requests[user_id]) >= self.requests_per_minute:
            return True
        
        # Add current request
        self.requests[user_id].append(now)
        return False


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=60)


async def check_rate_limit(request: Request, user_id: str):
    """Middleware to check rate limiting"""
    if rate_limiter.is_rate_limited(user_id):
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again in a minute."
        )