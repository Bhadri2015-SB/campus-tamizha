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


class ApplicationUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    mobile: str | None = None
    city: str | None = None
    dob: str | None = None
    gender: str | None = None
    qualification: str | None = None
    board: str | None = None
    year: int | None = None
    percentage: float | None = None
    college: str | None = None
    course: str | None = None
    admission_year: int | None = None
    notes: str | None = None
    status: str | None = None
    admin_notes: str | None = None
    
    class Config:
        from_attributes = True


class ApplicationResponse(ApplicationCreate):
    id: int
    status: str
    admin_notes: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CollegeBase(BaseModel):
    aishe_code: str
    name: str
    address: str | None = None
    state_name: str | None = None
    district_name: str | None = None
    website: str | None = None
    management: str | None = None
    year_of_establishment: str | None = None
    institution_type: str | None = None
    specialized_in: str | None = None
    university_id: str | None = None
    university_name: str | None = None
    university_type: str | None = None
    location: str | None = None
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