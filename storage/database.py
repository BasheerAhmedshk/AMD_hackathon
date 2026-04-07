import uuid
from datetime import datetime, timezone
import structlog
from sqlalchemy import Column, String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config.settings import settings

log = structlog.get_logger()

# 1. Initialize Async Engine
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False, 
    pool_size=10, 
    max_overflow=20
)

# 2. Session Factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# 3. Database Schema
class ThreatLog(Base):
    """Audit log for all Nadiaris Labs threat detections."""
    __tablename__ = 'threat_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    task = Column(String(50), nullable=False) # 'phishing' or 'malware'
    is_threat = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False) # CRITICAL, HIGH, MEDIUM, LOW
    provider_used = Column(String(50), nullable=False) # e.g., 'CUDAExecutionProvider'
    latency_ms = Column(Float, nullable=False)
    explanation_json = Column(JSONB, nullable=True) # Will hold Gemini 3-tier output

async def init_db():
    """Creates the tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database initialized successfully.")