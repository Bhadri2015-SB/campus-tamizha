from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.models.user import Base


class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True, nullable=False)
    mobile = Column(String(20), nullable=False)
    city = Column(String(100), nullable=False)
    dob = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    gender = Column(String(10), nullable=False)
    qualification = Column(String(100), nullable=False)
    board = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    college = Column(String(255), nullable=False)
    course = Column(String(255), nullable=False)
    admission_year = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, in_progress, approved, rejected
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
