import hashlib
import json
import redis.asyncio as redis
import structlog
from typing import Optional, Dict, Any
from config.settings import settings

log = structlog.get_logger()

# Connect to Redis
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def generate_cache_key(task: str, input_text: str) -> str:
    """Generates a secure, collision-resistant SHA-256 cache key."""
    normalized = f"{task}:{input_text.strip().lower()}"
    return hashlib.sha256(normalized.encode()).hexdigest()

async def get_cached_result(key: str) -> Optional[Dict[str, Any]]:
    """Fetches a result from Redis if it exists."""
    try:
        data = await redis_client.get(key)
        if data:
            log.debug("Cache hit", key=key)
            return json.loads(data)
        return None
    except Exception as e:
        log.warning("Redis GET failed, proceeding without cache", error=str(e))
        return None

async def set_cached_result(key: str, result: Dict[str, Any], ttl_seconds: int = 3600):
    """Saves a result to Redis with a 1-hour expiration by default."""
    try:
        await redis_client.set(key, json.dumps(result), ex=ttl_seconds)
        log.debug("Cache set", key=key, ttl=ttl_seconds)
    except Exception as e:
        log.warning("Redis SET failed", error=str(e))