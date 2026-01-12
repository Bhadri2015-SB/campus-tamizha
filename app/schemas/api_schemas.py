import datetime
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    name: str
    email: str
    mobile: str
    city: str
    dob: str
    gender: str
    qualification: str
    board: str
    year: int
    percentage: float
    college: str
    course: str
    admission_year: int
    notes: str | None = None
    
    class Config:
        from_attributes = True


class ApplicationResponse(ApplicationCreate):
    id: int
    status: str
    admin_notes: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CollegeBase(BaseModel):
    name: str
    city: str
    email: str
    whatsapp: str
    active: bool = True

    class Config:
        from_attributes = True


class CollegeResponse(CollegeBase):
    id: int


class TestimonialBase(BaseModel):
    quote: str
    name: str
    college: str
    avatar: str | None = None
    active: bool = True

    class Config:
        from_attributes = True


class TestimonialResponse(TestimonialBase):
    id: int