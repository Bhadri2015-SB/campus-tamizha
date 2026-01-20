from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.models.user import Base

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True, nullable=False)
    mobile = Column(String(20), nullable=False)
    city = Column(String(100), nullable=False)
    dob = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    gender = Column(String(10), nullable=False)
    sslc_percentage = Column(Float, nullable=False)
    hsc_percentage = Column(Float, nullable=False)
    school_name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False)
    # qualification = Column(String(100), nullable=False)
    board = Column(String(100), nullable=False)
    # year = Column(Integer, nullable=False)
    # percentage = Column(Float, nullable=False)
    college = Column(JSON, nullable=False)  # List of up to 3 colleges
    course = Column(JSON, nullable=False)  # List of up to 3 courses
    # admission_year = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, in_progress, approved, rejected
    admin_notes = Column(Text, nullable=True)
    admin_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(IST), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST), nullable=False)
    
    # Relationship to status history
    status_history = relationship("ApplicationStatusHistory", back_populates="application", cascade="all, delete-orphan")
