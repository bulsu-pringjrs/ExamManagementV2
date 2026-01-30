from core.database import Base
from sqlalchemy import Column, Float, Integer, String


class Results(Base):
    __tablename__ = "results"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    submission_id = Column(Integer, nullable=False)
    student_id = Column(Integer, nullable=False)
    exam_id = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(String, nullable=True)
    graded_at = Column(String, nullable=True)