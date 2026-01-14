from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.db.database import get_session
from app.core.deps import get_current_user, get_current_superuser
from app.core.config import settings
from app.models.user import User
from app.schemas.api_schemas import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from app.services import db_crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["Applications"])



@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application_data: ApplicationCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new application"""
    try:
        return await db_crud.create_application(session, application_data.model_dump())
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


@router.get("/", response_model=List[ApplicationResponse])
async def list_applications(
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "created_at",
    order: str = "desc",
    name: str = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """List all applications (admin only) with sorting and filtering
    
    Args:
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return
        sort_by: Field to sort by (id, name, email, city, status, created_at, etc.)
        order: Sort order (asc or desc)
        name: Filter by name (partial match, case-insensitive)
    """
    try:
        # Validate sort order
        if order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must be 'asc' or 'desc'"
            )
        
        return await db_crud.get_applications(
            session, skip, limit, sort_by, order, name
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
    """Update application status (admin only)"""
    try:
        # Validate status is from allowed options
        if status_update not in settings.APPLICATION_STATUS_OPTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(settings.APPLICATION_STATUS_OPTIONS)}"
            )
        
        application = await db_crud.update_application_status(
            session, application_id, status_update, admin_notes
        )
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        return application
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while updating application"
        )
    except Exception as e:
        logger.error(f"Unexpected error while updating application {application_id}: {str(e)}")
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


