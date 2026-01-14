from sqlalchemy import Column, Integer, String, Boolean, Text
from app.models.user import Base


class College(Base):
    __tablename__ = "colleges"
    
    id = Column(Integer, primary_key=True, index=True)
    aishe_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False, index=True)
    address = Column(Text, nullable=True)
    state_name = Column(String(100), nullable=True)
    district_name = Column(String(100), nullable=True, index=True)
    website = Column(String(255), nullable=True)
    management = Column(String(100), nullable=True)
    year_of_establishment = Column(String(10), nullable=True)
    institution_type = Column(String(100), nullable=True)
    specialized_in = Column(String(255), nullable=True)
    university_id = Column(String(50), nullable=True)
    university_name = Column(String(255), nullable=True, index=True)
    university_type = Column(String(100), nullable=True)
    location = Column(String(50), nullable=True)
    active = Column(Boolean, default=True, nullable=False)

