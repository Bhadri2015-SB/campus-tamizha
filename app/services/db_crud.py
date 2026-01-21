from typing import List, Optional
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.application import Application
from app.models.application_status_history import ApplicationStatusHistory
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
    limit: int = 10,
    sort_by: str = "created_at",
    order: str = "desc",
    name: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> tuple[List[Application], int]:
    """Get all applications with pagination, sorting, and filtering
    
    Args:
        session: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        sort_by: Field to sort by
        order: Sort order (asc or desc)
        name: Filter by name (partial match)
        location: Filter by city/location (partial match)
        status: Filter by application status
        start_date: Filter from date (format: YYYY-MM-DD)
        end_date: Filter until date (format: YYYY-MM-DD)
    
    Returns:
        tuple: (list of applications, total count)
    """
    try:
        # Build base query
        statement = select(Application)
        count_statement = select(Application)
        
        # Apply name filter if provided
        if name:
            statement = statement.where(Application.name.ilike(f"{name}%"))
            count_statement = count_statement.where(Application.name.ilike(f"{name}%"))
        
        # Apply location filter if provided
        if location:
            statement = statement.where(Application.city.ilike(f"{location}%"))
            count_statement = count_statement.where(Application.city.ilike(f"{location}%"))
        
        # Apply status filter if provided
        if status:
            statement = statement.where(Application.status == status)
            count_statement = count_statement.where(Application.status == status)
        
        # Apply date range filters if provided
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                statement = statement.where(Application.created_at >= start_datetime)
                count_statement = count_statement.where(Application.created_at >= start_datetime)
            except ValueError:
                logger.error(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD")
                raise ValueError(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD")
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                # Set to end of day
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                statement = statement.where(Application.created_at <= end_datetime)
                count_statement = count_statement.where(Application.created_at <= end_datetime)
            except ValueError:
                logger.error(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD")
                raise ValueError(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD")
        
        # Get total count
        from sqlalchemy import func
        count_result = await session.execute(select(func.count()).select_from(count_statement.subquery()))
        total = count_result.scalar()
        
        # Apply sorting
        sort_column = getattr(Application, sort_by, Application.created_at)
        if order == "desc":
            statement = statement.order_by(sort_column.desc())
        else:
            statement = statement.order_by(sort_column.asc())
        
        # Apply pagination
        statement = statement.offset(skip).limit(limit)
        
        result = await session.execute(statement)
        applications = result.scalars().all()
        
        return applications, total
    except AttributeError as e:
        logger.error(f"Invalid sort field: {sort_by}")
        raise ValueError(f"Invalid sort field: {sort_by}")
    except ValueError as e:
        logger.error(f"Validation error in get_applications: {str(e)}")
        raise
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
    admin_notes: Optional[str] = None,
    admin_name: Optional[str] = None
) -> Optional[Application]:
    """Update application status, admin notes, and admin name"""
    try:
        application = await session.get(Application, application_id)
        if not application:
            return None
        
        application.status = status_update
        if admin_notes:
            application.admin_notes = admin_notes
        if admin_name:
            application.admin_name = admin_name
        
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


async def update_application(
    session: AsyncSession,
    application_id: int,
    update_data: dict
) -> Optional[Application]:
    """Update application with full data from frontend"""
    try:
        logger.info(f"Attempting to update application {application_id}")
        
        application = await session.get(Application, application_id)
        if not application:
            logger.warning(f"Application {application_id} not found for update")
            return None
        
        logger.debug(f"Current application data: {application.__dict__}")
        
        # Update all provided fields
        updated_fields = []
        for field, value in update_data.items():
            if hasattr(application, field):
                old_value = getattr(application, field)
                if old_value != value:
                    setattr(application, field, value)
                    updated_fields.append(field)
                    logger.debug(f"Updated field '{field}': {old_value} -> {value}")
        
        if not updated_fields:
            logger.info(f"No fields changed for application {application_id}")
        else:
            logger.info(f"Updated fields for application {application_id}: {', '.join(updated_fields)}")
        
        session.add(application)
        await session.commit()
        await session.refresh(application)
        
        logger.info(f"Successfully updated application {application_id}")
        return application
        
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error while updating application {application_id}: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error while updating application {application_id}: {str(e)}", exc_info=True)
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
    limit: int = 10,
    active_only: bool = True,
    search: Optional[str] = None
) -> tuple[List[College], int]:
    """Get all colleges with pagination and name search
    
    Returns:
        tuple: (list of colleges, total count)
    """
    try:
        # Build base query
        statement = select(College)
        count_statement = select(College)
        
        # Apply active filter
        if active_only:
            statement = statement.where(College.active == True)
            count_statement = count_statement.where(College.active == True)
        
        # Apply search filter (searches in college name only)
        if search:
            search_filter = f"{search}%"
            statement = statement.where(College.name.ilike(search_filter))
            count_statement = count_statement.where(College.name.ilike(search_filter))
        
        # Get total count
        from sqlalchemy import func
        count_result = await session.execute(select(func.count()).select_from(count_statement.subquery()))
        total = count_result.scalar()
        
        # Apply pagination and ordering
        statement = statement.order_by(College.name.asc()).offset(skip).limit(limit)
        
        # Execute query
        result = await session.execute(statement)
        colleges = result.scalars().all()
        
        return colleges, total
        
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
    limit: int = 10,
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


# Application Status History CRUD Operations
async def create_status_history(
    session: AsyncSession,
    application_id: int,
    status: str,
    admin_email: str,
    admin_name: str = None,
    notes: str = None
) -> ApplicationStatusHistory:
    """Create a new status history entry"""
    try:
        status_history = ApplicationStatusHistory(
            application_id=application_id,
            status=status,
            admin_email=admin_email,
            admin_name=admin_name,
            notes=notes
        )
        session.add(status_history)
        await session.commit()
        await session.refresh(status_history)
        return status_history
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error creating status history: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error creating status history: {str(e)}")
        raise


async def get_application_status_history(
    session: AsyncSession,
    application_id: int
) -> List[ApplicationStatusHistory]:
    """Get all status history for an application"""
    try:
        statement = select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application_id
        ).order_by(ApplicationStatusHistory.created_at.desc())
        
        result = await session.execute(statement)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching status history for application {application_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching status history for application {application_id}: {str(e)}")
        raise
