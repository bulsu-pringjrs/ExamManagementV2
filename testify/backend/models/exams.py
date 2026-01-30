from core.database import Base
from sqlalchemy import Column, Integer, String


class Exams(Base):
    __tablename__ = "exams"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    class_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    total_score = Column(Integer, nullable=False)
    questions = Column(String, nullable=False)
    availability_status = Column(String, nullable=False)
    created_by = Column(Integer, nullable=False)
    created_at = Column(String, nullable=True)
    