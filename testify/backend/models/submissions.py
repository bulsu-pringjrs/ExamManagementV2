from core.database import Base
from sqlalchemy import Boolean, Column, Float, Integer, String


class Submissions(Base):
    __tablename__ = "submissions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    exam_id = Column(Integer, nullable=False)
    student_id = Column(Integer, nullable=False)
    answers = Column(String, nullable=False)
    submitted_at = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    graded = Column(Boolean, nullable=True)