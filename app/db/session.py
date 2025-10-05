from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Optimized connection pool for DigitalOcean constraints (2-4GB RAM)
# Reduced pool size to minimize memory footprint while maintaining performance
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=5,  # Base connections (reduced from 10 for memory efficiency)
    max_overflow=15,  # Additional connections under load (reduced from 20)
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Timeout for getting connection from pool
    echo=settings.app_env == "development"  # Log SQL queries in development
)

# Connection pool monitoring
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log when new connections are created"""
    logger.debug("Database connection established")

@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when connections are checked out from pool"""
    logger.debug("Connection checked out from pool")

@event.listens_for(Pool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log when connections are returned to pool"""
    logger.debug("Connection returned to pool")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_connection_pool_stats():
    """Get current connection pool statistics for monitoring"""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
        "max_overflow": engine.pool._max_overflow,
        "timeout": engine.pool._timeout
    }


def check_database_health():
    """Check database connectivity and pool health"""
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Get pool stats
        stats = get_connection_pool_stats()
        
        # Check if pool is healthy
        is_healthy = stats["checked_out"] < (stats["pool_size"] + stats["max_overflow"])
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "pool_stats": stats
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


