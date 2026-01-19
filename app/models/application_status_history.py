from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.user import Base


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # pending, in_progress, approved, rejected
    admin_email = Column(String(255), nullable=False)  # Email of admin who made the change
    admin_name = Column(String(255), nullable=True)  # Name of admin (optional)
    notes = Column(Text, nullable=True)  # Admin notes about the status change
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to Application
    application = relationship("Application", back_populates="status_history")
