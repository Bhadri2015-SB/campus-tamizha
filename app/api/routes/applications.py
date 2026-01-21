from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel
from app.db.database import get_session
from app.core.deps import get_current_user, get_current_superuser
from app.core.config import settings
from app.models.user import User
from app.schemas.api_schemas import (
    ApplicationCreate, 
    ApplicationResponse, 
    ApplicationUpdate,
    ApplicationStatusHistoryCreate,
    ApplicationStatusHistoryResponse
)
from app.services import db_crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["Applications"])


class PaginatedApplicationResponse(BaseModel):
    """Paginated response for applications"""
    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int



@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application_data: ApplicationCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new application"""
    try:
        # Create the application
        application = await db_crud.create_application(session, application_data.model_dump())
        
        # Create initial status history entry for "pending" status
        await db_crud.create_status_history(
            session=session,
            application_id=application.id,
            status="pending",
            admin_email="system@campustamizha.com",
            admin_name="System",
            notes="Application submitted"
        )
        
        return application
    except IntegrityError as e:
        logger.error(f"Database integrity error while creating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid application data or duplicate entry"
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while creating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while creating application"
        )
    except Exception as e:
        logger.error(f"Unexpected error while creating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/", response_model=PaginatedApplicationResponse)
async def list_applications(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    order: str = Query("desc", description="Sort order (asc or desc)"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    location: Optional[str] = Query(None, description="Filter by city/location"),
    application_status: Optional[str] = Query(None, description="Filter by application status"),
    start_date: Optional[str] = Query(None, description="Filter applications from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter applications until this date (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """List all applications (admin only) with pagination, sorting and filtering
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page
        sort_by: Field to sort by (id, name, email, city, status, created_at, etc.)
        order: Sort order (asc or desc)
        name: Filter by name (partial match, case-insensitive)
        location: Filter by city/location (partial match, case-insensitive)
        application_status: Filter by application status
        start_date: Filter applications from this date (format: YYYY-MM-DD)
        end_date: Filter applications until this date (format: YYYY-MM-DD)
    """
    try:
        # Validate sort order
        if order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must be 'asc' or 'desc'"
            )
        
        # Validate status if provided
        if application_status and application_status not in settings.APPLICATION_STATUS_OPTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(settings.APPLICATION_STATUS_OPTIONS)}"
            )
        
        # Calculate skip based on page
        skip = (page - 1) * page_size
        
        # Fetch applications with filters
        applications, total = await db_crud.get_applications(
            session, skip, page_size, sort_by, order, name, location, application_status, start_date, end_date
        )
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return PaginatedApplicationResponse(
            items=applications,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while listing applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching applications"
        )
    except Exception as e:
        logger.error(f"Unexpected error while listing applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """Get application by ID (admin only)"""
    try:
        application = await db_crud.get_application_by_id(session, application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        return application
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching application"
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    status_update: str,
    admin_notes: str = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """Update application status (admin only)
    
    Updates the application status and automatically creates a status history entry
    to track the change with admin details and timestamp.
    """
    try:
        logger.info(f"Admin {current_user.email} updating status for application {application_id}")
        
        # Validate status is from allowed options
        if status_update not in settings.APPLICATION_STATUS_OPTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(settings.APPLICATION_STATUS_OPTIONS)}"
            )
        
        # Verify application exists
        application = await db_crud.get_application_by_id(session, application_id)
        if not application:
            logger.warning(f"Application {application_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Create status history entry with username from token
        await db_crud.create_status_history(
            session=session,
            application_id=application_id,
            status=status_update,
            admin_email=current_user.email,
            admin_name=current_user.username,
            notes=admin_notes
        )
        
        # Update the application's current status
        application = await db_crud.update_application_status(
            session, application_id, status_update, admin_notes, current_user.username
        )
        
        logger.info(f"Successfully updated application {application_id} status to {status_update}")
        return application
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating application {application_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while updating application"
        )
    except Exception as e:
        logger.error(f"Unexpected error while updating application {application_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application_data(
    application_id: int,
    update_data: ApplicationUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """Update full application data (admin only)
    
    Frontend passes the entire application object with all fields.
    Updates all provided fields in the application including:
    - Personal info: name, email, mobile, city, dob, gender
    - Academic info: qualification, board, year, percentage
    - College info: college, course, admission_year
    - Notes and status: notes, status, admin_notes
    """
    try:
        logger.info(f"Admin {current_user.email} attempting to update application {application_id}")
        
        # Convert Pydantic model to dict, excluding unset values
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            logger.warning(f"No data provided for updating application {application_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
        logger.debug(f"Update data for application {application_id}: {update_dict}")
        
        # Validate status if provided
        if "status" in update_dict and update_dict["status"] not in settings.APPLICATION_STATUS_OPTIONS:
            logger.warning(f"Invalid status '{update_dict['status']}' provided for application {application_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(settings.APPLICATION_STATUS_OPTIONS)}"
            )
        
        # Call database function to update application
        application = await db_crud.update_application(
            session, application_id, update_dict
        )
        
        if not application:
            logger.warning(f"Application {application_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        logger.info(f"Successfully updated application {application_id} by admin {current_user.email}")
        return application
        
    except HTTPException as e:
        logger.error(f"HTTP error while updating application {application_id}: {e.status_code} - {e.detail}")
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating application {application_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while updating application"
        )
    except ValueError as e:
        logger.error(f"Validation error while updating application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error while updating application {application_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/{application_id}/status-history", response_model=List[ApplicationStatusHistoryResponse])
async def get_status_history(
    application_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """Get all status history for an application (admin only)
    
    Returns a list of all status changes for the application,
    ordered from newest to oldest. Each entry includes:
    - Status value
    - Admin who made the change
    - Notes about the change
    - Timestamp
    """
    try:
        logger.info(f"Admin {current_user.email} fetching status history for application {application_id}")
        
        # Verify application exists
        application = await db_crud.get_application_by_id(session, application_id)
        if not application:
            logger.warning(f"Application {application_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Get status history
        history = await db_crud.get_application_status_history(session, application_id)
        
        logger.info(f"Successfully fetched {len(history)} status history entries for application {application_id}")
        return history
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching status history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching status history"
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching status history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
