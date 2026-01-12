# SQLAlchemy Base and models for Alembic
from app.models.user import Base

# Import all models to register them with Base metadata
from app.models.user import User
from app.models.application import Application
from app.models.college import College
from app.models.testimonial import Testimonial

# This allows Alembic to detect all models
target_metadata = Base.metadata
