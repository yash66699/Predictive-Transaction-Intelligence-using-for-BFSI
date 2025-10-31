# database.py - Database connection and session management
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.config import DATABASE_URL
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async engine with enhanced configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30
)

# Create async session maker
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Create declarative base for ORM models
Base = declarative_base()

async def connect_db():
    """Initialize database and create all tables"""
    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they are registered
            from app.models import (
                User, Transaction, FraudAlert, ChatHistory, 
                UserSettings, FileUpload, RuleEngine, ModelMetrics, SystemLog
            )
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database connected and tables created successfully")
            
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        raise

async def disconnect_db():
    """Close database connections"""
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

async def get_db_session() -> AsyncSession:
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected session error: {e}")
            raise
        finally:
            await session.close()



async def check_db_health() -> dict:
    try:
        async with engine.begin() as conn:
            # Use text() for raw SQL
            result = await conn.execute(text("SELECT version()"))
            version_row = result.fetchone()
            version = version_row[0] if version_row else "Unknown"

            # Count tables in public schema
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables_result = await conn.execute(tables_query)
            tables = tables_result.fetchall()
            table_count = len(tables)

            return {
                "status": "healthy",
                "database_version": version,
                "table_count": table_count,
                "connection_pool": {
                    "size": engine.pool.size(),
                    "checked_out": engine.pool.checkedout(),
                    "checked_in": engine.pool.checkedin()
                }
            }
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


class DatabaseManager:
    """Database manager for handling connections and operations"""
    
    @staticmethod
    async def execute_raw_query(query: str, params: dict = None):
        """Execute raw SQL query"""
        try:
            async with async_session() as session:
                result = await session.execute(query, params)
                await session.commit()
                return result
        except Exception as e:
            logger.error(f"Error executing raw query: {e}")
            raise
    
    @staticmethod
    async def backup_database():
        """Create database backup (implementation depends on your needs)"""
        # This would typically involve calling pg_dump or similar
        logger.info("Database backup initiated")
        # Implementation here
        pass
    
    @staticmethod
    async def get_table_statistics():
        """Get statistics for all tables"""
        try:
            async with async_session() as session:
                stats = {}
                
                # Get row counts for main tables
                tables = ['users', 'transactions', 'fraud_alerts', 'chat_history']
                
                for table in tables:
                    result = await session.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    stats[table] = count
                
                return stats
        except Exception as e:
            logger.error(f"Error getting table statistics: {e}")
            return {}

# Global database manager instance
db_manager = DatabaseManager()
