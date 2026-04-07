from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from storage.database import Base

class ThreatAudit(Base):
    __tablename__ = 'threat_audits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_snippet = Column(Text, nullable=False)
    ai_analysis = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
