from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.db.database import get_session
from app.core.deps import get_current_user, get_current_superuser
from app.core.config import settings
from app.models.user import User
from app.schemas.api_schemas import ApplicationCreate, ApplicationResponse
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
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """List all applications (admin only)"""
    try:
        return await db_crud.get_applications(session, skip, limit)
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
async def update_application(
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


