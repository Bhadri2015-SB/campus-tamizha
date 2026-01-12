from sqlalchemy import Column, Integer, String, Boolean
from app.models.user import Base


class College(Base):
    __tablename__ = "colleges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    city = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    whatsapp = Column(String(20), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
