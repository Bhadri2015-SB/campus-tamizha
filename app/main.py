import logging
import time
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api.routes import applications, auth, colleges, testimonials
from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.db.database import create_db_and_tables, close_db

# Initialize logging
setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    logger.info("Starting up campus Tamizha application...")
    try:
        await create_db_and_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise
    
    logger.info(f"Application startup complete - {settings.APP_NAME} v{settings.APP_VERSION}")
    yield

    # Shutdown
    logger.info("Shutting down application...")
    try:
        await close_db()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error during database shutdown: {str(e)}", exc_info=True)
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Campus Tamizha - College Admission Management System",
    lifespan=lifespan
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log response
        logger.info(f"Request: {request.method} {request.url.path} | Status: {response.status_code} | Duration: {duration:.3f}s")
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(duration)
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} | "
            f"Duration: {duration:.3f}s | Error: {str(e)}",
            exc_info=True
        )
        raise


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    # Log validation errors at ERROR level
    logger.error(
        f"Validation error: {request.method} {request.url.path} | "
        f"Errors: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body if hasattr(exc, 'body') else None
        }
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    # Don't log HTTPException as unhandled errors - they're expected API responses
    if isinstance(exc, HTTPException):
        # Only log authentication/authorization failures at INFO level
        if exc.status_code in (401, 403):
            logger.info(
                f"Authentication/Authorization: {request.method} {request.url.path} | "
                f"Status: {exc.status_code} | Detail: {exc.detail}"
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # Log actual unexpected errors
    logger.error(
        f"Unhandled exception: {request.method} {request.url.path} | "
        f"Error: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error occurred",
            "type": type(exc).__name__
        }
    )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS middleware configured")

# Register routers
app.include_router(auth.router, prefix="/api")
logger.info("Auth router registered")
app.include_router(applications.router, prefix="/api")
logger.info("Applications router registered")
app.include_router(colleges.router, prefix="/api")
logger.info("Colleges router registered")
app.include_router(testimonials.router, prefix="/api")
logger.info("Testimonials router registered")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    logger.debug("Root endpoint accessed")
    return {
        "message": "Welcome to campus Tamizha API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
