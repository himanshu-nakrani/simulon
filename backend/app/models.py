from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from backend.app.db import Base


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_text = Column(String, nullable=False)
    structured_json = Column(String, nullable=False)
    result_json = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
