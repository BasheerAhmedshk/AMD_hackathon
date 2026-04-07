import asyncio
import structlog
from sqlalchemy import text
from storage.database import engine, init_db
from storage.cache import redis_client

log = structlog.get_logger()

async def test_all():
    log.info("Starting Phase 2 Connection Tests...")

    # Test 1: Redis
    try:
        ping = await redis_client.ping()
        log.info("✅ Redis Connection: SUCCESS", ping=ping)
    except Exception as e:
        log.error("❌ Redis Connection: FAILED", error=str(e))

    # Test 2: PostgreSQL
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            log.info("✅ PostgreSQL Connection: SUCCESS", version=version[:25] + "...")
        
        # Initialize tables
        await init_db()
    except Exception as e:
        log.error("❌ PostgreSQL Connection: FAILED", error=str(e))

if __name__ == "__main__":
    asyncio.run(test_all())