from core.database import Base
from sqlalchemy import Column, Integer, String


class Classes(Base):
    __tablename__ = "classes"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    class_name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    teacher_id = Column(Integer, nullable=False)
    student_ids = Column(String, nullable=True)
    created_at = Column(String, nullable=True)