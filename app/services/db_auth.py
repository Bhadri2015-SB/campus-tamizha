from typing import Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User

logger = logging.getLogger(__name__)


async def get_user_by_username(
    session: AsyncSession, 
    username: str
) -> Optional[User]:
    """Get user by username"""
    try:
        statement = select(User).where(User.username == username)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by username '{username}': {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching user by username '{username}': {str(e)}")
        raise


async def get_user_by_email(
    session: AsyncSession, 
    email: str
) -> Optional[User]:
    """Get user by email"""
    try:
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by email '{email}': {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching user by email '{email}': {str(e)}")
        raise


async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    hashed_password: str,
    is_superuser: bool = False
) -> User:
    """Create a new user"""
    try:
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_superuser=is_superuser
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error creating user '{username}': {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error creating user '{username}': {str(e)}")
        raise
