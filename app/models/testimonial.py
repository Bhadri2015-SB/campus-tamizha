from sqlalchemy import Column, Integer, String, Boolean, Text
from app.models.user import Base


class Testimonial(Base):
    __tablename__ = "testimonials"
    
    id = Column(Integer, primary_key=True, index=True)
    quote = Column(Text, nullable=False)
    name = Column(String(255), nullable=False)
    college = Column(String(255), nullable=False)
    avatar = Column(String(500), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
