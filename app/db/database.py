import logging
from typing import AsyncGenerator
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.models.user import Base

logger = logging.getLogger(__name__)

# Create async engine
# For SQLite, use aiosqlite driver
database_url = settings.DATABASE_URL

logger.info(f"Configuring database connection: {database_url.split('://')[0]}://...")

# Enable SQL query logging if configured
echo_sql = settings.DEBUG or getattr(settings, 'LOG_SQL_QUERIES', False)

engine = create_async_engine(
    database_url,
    echo=echo_sql,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

logger.info("Database engine and session factory initialized")


async def create_db_and_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating database tables: {str(e)}", exc_info=True)
        raise


async def close_db():
    """Close database connection and dispose engine"""
    try:
        logger.info("Closing database connections...")
        await engine.dispose()
        logger.info("Database connections closed and engine disposed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}", exc_info=True)
        raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    logger.debug("Creating new database session")
    async with AsyncSessionLocal() as session:
        try:
            yield session
            logger.debug("Database session completed successfully")
        except (HTTPException, RequestValidationError):
            # HTTPException is used for API responses (401, 403, 404, etc.)
            # RequestValidationError is for invalid request data (Pydantic validation)
            # These are not database errors, so just re-raise without logging
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in database session: {str(e)}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Database session closed")
