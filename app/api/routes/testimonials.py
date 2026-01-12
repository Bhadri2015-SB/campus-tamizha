from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.db.database import get_session
from app.core.deps import get_current_superuser
from app.models.user import User
from app.schemas.api_schemas import TestimonialBase, TestimonialResponse
from app.services import db_crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/testimonials", tags=["Testimonials"])


@router.get("/", response_model=List[TestimonialResponse])
async def list_testimonials(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    session: AsyncSession = Depends(get_session)
):
    """List all testimonials"""
    try:
        return await db_crud.get_testimonials(session, skip, limit, active_only)
    except SQLAlchemyError as e:
        logger.error(f"Database error while listing testimonials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching testimonials"
        )
    except Exception as e:
        logger.error(f"Unexpected error while listing testimonials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/{testimonial_id}", response_model=TestimonialResponse)
async def get_testimonial(
    testimonial_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get testimonial by ID"""
    try:
        testimonial = await db_crud.get_testimonial_by_id(session, testimonial_id)
        if not testimonial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Testimonial not found"
            )
        return testimonial
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching testimonial {testimonial_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while fetching testimonial"
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching testimonial {testimonial_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

