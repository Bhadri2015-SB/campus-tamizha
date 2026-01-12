from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.application import Application
from app.models.college import College
from app.models.testimonial import Testimonial

logger = logging.getLogger(__name__)


# Application CRUD Operations
async def create_application(session: AsyncSession, application_data: dict) -> Application:
    """Create a new application"""
    try:
        application = Application(**application_data)
        session.add(application)
        await session.commit()
        await session.refresh(application)
        return application
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error creating application: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error creating application: {str(e)}")
        raise


async def get_applications(
    session: AsyncSession, 
    skip: int = 0, 
    limit: int = 100
) -> List[Application]:
    """Get all applications with pagination"""
    try:
        statement = select(Application).offset(skip).limit(limit)
        result = await session.execute(statement)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching applications: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching applications: {str(e)}")
        raise


async def get_application_by_id(
    session: AsyncSession, 
    application_id: int
) -> Optional[Application]:
    """Get application by ID"""
    try:
        return await session.get(Application, application_id)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching application {application_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching application {application_id}: {str(e)}")
        raise


async def update_application_status(
    session: AsyncSession,
    application_id: int,
    status_update: str,
    admin_notes: Optional[str] = None
) -> Optional[Application]:
    """Update application status and admin notes"""
    try:
        application = await session.get(Application, application_id)
        if not application:
            return None
        
        application.status = status_update
        if admin_notes:
            application.admin_notes = admin_notes
        
        session.add(application)
        await session.commit()
        await session.refresh(application)
        return application
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error updating application {application_id}: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error updating application {application_id}: {str(e)}")
        raise


# College CRUD Operations
async def create_college(session: AsyncSession, college_data: dict) -> College:
    """Create a new college"""
    try:
        college = College(**college_data)
        session.add(college)
        await session.commit()
        await session.refresh(college)
        return college
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error creating college: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error creating college: {str(e)}")
        raise


async def get_colleges(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> List[College]:
    """Get all colleges with pagination and optional active filter"""
    try:
        statement = select(College)
        if active_only:
            statement = statement.where(College.active == True)
        statement = statement.offset(skip).limit(limit)
        result = await session.execute(statement)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching colleges: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching colleges: {str(e)}")
        raise


async def get_college_by_id(
    session: AsyncSession, 
    college_id: int
) -> Optional[College]:
    """Get college by ID"""
    try:
        return await session.get(College, college_id)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching college {college_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching college {college_id}: {str(e)}")
        raise


async def update_college(
    session: AsyncSession,
    college_id: int,
    college_data: dict
) -> Optional[College]:
    """Update college by ID"""
    try:
        college = await session.get(College, college_id)
        if not college:
            return None
        
        for key, value in college_data.items():
            setattr(college, key, value)
        
        session.add(college)
        await session.commit()
        await session.refresh(college)
        return college
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error updating college {college_id}: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error updating college {college_id}: {str(e)}")
        raise


async def delete_college(
    session: AsyncSession, 
    college_id: int
) -> bool:
    """Delete college by ID"""
    try:
        college = await session.get(College, college_id)
        if not college:
            return False
        
        await session.delete(college)
        await session.commit()
        return True
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error deleting college {college_id}: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error deleting college {college_id}: {str(e)}")
        raise


# Testimonial CRUD Operations
async def create_testimonial(session: AsyncSession, testimonial_data: dict) -> Testimonial:
    """Create a new testimonial"""
    try:
        testimonial = Testimonial(**testimonial_data)
        session.add(testimonial)
        await session.commit()
        await session.refresh(testimonial)
        return testimonial
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error creating testimonial: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error creating testimonial: {str(e)}")
        raise


async def get_testimonials(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> List[Testimonial]:
    """Get all testimonials with pagination and optional active filter"""
    try:
        statement = select(Testimonial)
        if active_only:
            statement = statement.where(Testimonial.active == True)
        statement = statement.offset(skip).limit(limit)
        result = await session.execute(statement)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching testimonials: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching testimonials: {str(e)}")
        raise


async def get_testimonial_by_id(
    session: AsyncSession, 
    testimonial_id: int
) -> Optional[Testimonial]:
    """Get testimonial by ID"""
    try:
        return await session.get(Testimonial, testimonial_id)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching testimonial {testimonial_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching testimonial {testimonial_id}: {str(e)}")
        raise


async def update_testimonial(
    session: AsyncSession,
    testimonial_id: int,
    testimonial_data: dict
) -> Optional[Testimonial]:
    """Update testimonial by ID"""
    try:
        testimonial = await session.get(Testimonial, testimonial_id)
        if not testimonial:
            return None
        
        for key, value in testimonial_data.items():
            setattr(testimonial, key, value)
        
        session.add(testimonial)
        await session.commit()
        await session.refresh(testimonial)
        return testimonial
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error updating testimonial {testimonial_id}: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error updating testimonial {testimonial_id}: {str(e)}")
        raise


async def delete_testimonial(
    session: AsyncSession, 
    testimonial_id: int
) -> bool:
    """Delete testimonial by ID"""
    try:
        testimonial = await session.get(Testimonial, testimonial_id)
        if not testimonial:
            return False
        
        await session.delete(testimonial)
        await session.commit()
        return True
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error deleting testimonial {testimonial_id}: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error deleting testimonial {testimonial_id}: {str(e)}")
        raise
