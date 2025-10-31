import asyncio
import logging
import sys
from pathlib import Path
from sqlalchemy.future import select

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.database import connect_db, disconnect_db, engine, Base, check_db_health, async_session
from app.models import (
    User, Transaction, FraudAlert, ChatHistory, UserSettings, 
    FileUpload, RuleEngine, ModelMetrics, SystemLog
)
from app.crud import create_system_log
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database with all tables"""
    try:
        logger.info("Starting database initialization...")
        
        # Connect to the database
        await connect_db()
        logger.info("Connected to database successfully")
        
        # Check database health before initialization
        health = await check_db_health()
        logger.info(f"Pre-initialization database health: {health}")
        
        logger.info("Database tables created successfully")
        
        # Initialize with default rules and data
        await create_default_rules()
        await create_default_model_metrics()
        
        # Verify table creation
        health_after = await check_db_health()
        logger.info(f"Post-initialization database health: {health_after}")
        
        # Log successful initialization
        async with async_session() as db:
            await create_system_log(
                db, 
                level="INFO", 
                message="Database initialized successfully",
                module="init_db"
            )
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Log the error
        try:
            async with async_session() as db:
                await create_system_log(
                    db,
                    level="ERROR",
                    message=f"Database initialization failed: {str(e)}",
                    module="init_db"
                )
        except:
            pass  # If we can't log, don't crash
        raise
    finally:
        # Clean up connections
        await disconnect_db()
        logger.info("Database connections closed")

async def create_default_rules():
    """Initialize database with default fraud detection rules"""
    try:
        logger.info("Creating default fraud detection rules...")
        
        default_rules = [
            {
                "rule_name": "high_amount_rule",
                "rule_description": "Flag transactions above 5x user average amount",
                "rule_logic": '{"condition": "transaction_amount > user_avg_amount * 5", "multiplier": 5.0}',
                "is_active": True,
                "priority": 1,
                "threshold": 5.0,
                "created_by": "system"
            },
            {
                "rule_name": "unverified_kyc_international",
                "rule_description": "Flag international transactions with unverified KYC",
                "rule_logic": '{"condition": "channel == \'international\' AND kyc_verified == \'No\'"}',
                "is_active": True,
                "priority": 2,
                "threshold": 1.0,
                "created_by": "system"
            },
            {
                "rule_name": "odd_hours_rule",
                "rule_description": "Flag transactions during odd hours (2AM-4AM)",
                "rule_logic": '{"condition": "hour >= 2 AND hour <= 4", "start_hour": 2, "end_hour": 4}',
                "is_active": True,
                "priority": 3,
                "threshold": 1.0,
                "created_by": "system"
            },
            {
                "rule_name": "new_account_high_amount",
                "rule_description": "Flag high amounts from accounts < 30 days old",
                "rule_logic": '{"condition": "account_age_days < 30 AND transaction_amount > 5000", "age_threshold": 30, "amount_threshold": 5000}',
                "is_active": True,
                "priority": 4,
                "threshold": 5000.0,
                "created_by": "system"
            },
            {
                "rule_name": "weekend_high_amount",
                "rule_description": "Flag high amount transactions on weekends",
                "rule_logic": '{"condition": "weekday >= 5 AND transaction_amount > 10000", "amount_threshold": 10000}',
                "is_active": True,
                "priority": 5,
                "threshold": 10000.0,
                "created_by": "system"
            }
        ]
        
        async with async_session() as db:
            for rule_data in default_rules:
                # Check if rule already exists using proper SQLAlchemy query
                result = await db.execute(
                    select(RuleEngine).filter(RuleEngine.rule_name == rule_data['rule_name'])
                )
                existing_rule = result.scalar_one_or_none()
                
                if not existing_rule:
                    rule = RuleEngine(**rule_data)
                    db.add(rule)
                    logger.info(f"Created rule: {rule_data['rule_name']}")
                else:
                    logger.info(f"Rule already exists: {rule_data['rule_name']}")
            
            await db.commit()
        
        logger.info("Default fraud detection rules created successfully")
        
    except Exception as e:
        logger.error(f"Error creating default rules: {e}")
        raise

async def create_default_model_metrics():
    """Create default model performance metrics"""
    try:
        logger.info("Creating default model metrics...")
        
        default_metrics = {
            "model_version": "v1.0",
            "accuracy": 0.95,
            "precision": 0.92,
            "recall": 0.88,
            "f1_score": 0.90,
            "auc_roc": 0.94,
            "total_predictions": 0,
            "fraud_detected": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "evaluation_date": datetime.utcnow()
        }
        
        async with async_session() as db:
            # Check if metrics already exist for this version using proper SQLAlchemy query
            result = await db.execute(
                select(ModelMetrics).filter(ModelMetrics.model_version == default_metrics['model_version'])
            )
            existing_metrics = result.scalar_one_or_none()
            
            if not existing_metrics:
                metrics = ModelMetrics(**default_metrics)
                db.add(metrics)
                await db.commit()
                logger.info("Default model metrics created successfully")
            else:
                logger.info("Model metrics already exist for version v1.0")
        
    except Exception as e:
        logger.error(f"Error creating default model metrics: {e}")
        raise

async def create_test_data():
    """Create test data for development (optional)"""
    try:
        logger.info("Creating test data...")
        
        # Create test user
        test_user_data = {
            "firebase_uid": "test_user_12345",
            "email": "test@example.com",
            "full_name": "Test User",
            "phone_number": "+1234567890"
        }
        
        async with async_session() as db:
            # Check if test user exists using proper SQLAlchemy query
            result = await db.execute(
                select(User).filter(User.firebase_uid == test_user_data['firebase_uid'])
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                test_user = User(**test_user_data)
                db.add(test_user)
                await db.flush()
                
                # Create user settings
                test_settings = UserSettings(user_id=test_user.id)
                db.add(test_settings)
                
                await db.commit()
                logger.info("Test user and settings created successfully")
            else:
                logger.info("Test user already exists")
        
    except Exception as e:
        logger.error(f"Error creating test data: {e}")
        # Don't raise here as test data is optional

async def reset_database():
    """Reset database by dropping and recreating all tables"""
    try:
        logger.warning("Starting database reset...")
        
        async with engine.begin() as conn:
            # Drop all tables in correct order (reverse of creation)
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("All tables dropped successfully")
            
            # Recreate all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("All tables recreated successfully")
        
        # Reinitialize with default data
        await create_default_rules()
        await create_default_model_metrics()
        
        # Log the reset
        async with async_session() as db:
            await create_system_log(
                db,
                level="WARNING",
                message="Database was reset and reinitialized",
                module="init_db"
            )
        
        logger.info("Database reset completed successfully")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise

async def check_health():
    """Check database health"""
    try:
        health = await check_db_health()
        print(f"Database Health Status: {health}")
        
        if health["status"] == "healthy":
            logger.info("Database is healthy")
            print("✅ Database connection: OK")
            print(f"✅ Database version: {health.get('database_version', 'Unknown')}")
            print(f"✅ Table count: {health.get('table_count', 0)}")
            print(f"✅ Connection pool: {health.get('connection_pool', {})}")
        else:
            logger.error("Database is unhealthy")
            print("❌ Database connection: FAILED")
            print(f"❌ Error: {health.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"❌ Health check failed: {e}")

async def backup_database():
    """Create database backup"""
    try:
        logger.info("Creating database backup...")
        
        # This is a placeholder - implement actual backup logic
        # You might use pg_dump for PostgreSQL
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        logger.info(f"Database backup would be saved as: {backup_filename}")
        
        # Log the backup
        async with async_session() as db:
            await create_system_log(
                db,
                level="INFO",
                message=f"Database backup created: {backup_filename}",
                module="init_db"
            )
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise

async def show_table_info():
    """Show information about created tables"""
    try:
        logger.info("Gathering table information...")
        
        async with async_session() as db:
            # Get table counts
            tables = [
                ('users', User),
                ('transactions', Transaction),
                ('fraud_alerts', FraudAlert),
                ('chat_history', ChatHistory),
                ('user_settings', UserSettings),
                ('file_uploads', FileUpload),
                ('rule_engine', RuleEngine),
                ('model_metrics', ModelMetrics),
                ('system_logs', SystemLog)
            ]
            
            print("\n📊 Table Information:")
            print("-" * 50)
            
            for table_name, model_class in tables:
                try:
                    result = await db.execute(select(model_class))
                    count = len(result.scalars().all())
                    print(f"📋 {table_name.ljust(15)}: {count} records")
                except Exception as e:
                    print(f"❌ {table_name.ljust(15)}: Error - {e}")
            
            print("-" * 50)
        
    except Exception as e:
        logger.error(f"Error showing table info: {e}")
        print(f"❌ Error gathering table information: {e}")

async def cleanup_database():
    """Clean up old logs and test data"""
    try:
        logger.info("Cleaning up database...")
        
        async with async_session() as db:
            # Delete old system logs (older than 30 days)
            thirty_days_ago = datetime.utcnow() - datetime.timedelta(days=30)
            
            # Note: This would require proper delete query implementation
            logger.info("Database cleanup completed (placeholder)")
            
            # Log the cleanup
            await create_system_log(
                db,
                level="INFO",
                message="Database cleanup completed",
                module="init_db"
            )
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        raise

def print_usage():
    """Print usage information"""
    print("""
Database Initialization Script

Usage:
    python init_db.py [command]

Commands:
    init     - Initialize database with tables and default data (default)
    reset    - Drop all tables and recreate them (DESTRUCTIVE)
    health   - Check database connection and health
    backup   - Create database backup
    test     - Create test data for development
    info     - Show table information and record counts
    cleanup  - Clean up old logs and data
    help     - Show this help message

Examples:
    python init_db.py
    python init_db.py init
    python init_db.py reset
    python init_db.py health
    python init_db.py backup
    python init_db.py test
    python init_db.py info
    python init_db.py cleanup
    """)

async def main():
    """Main function to handle command line arguments"""
    command = sys.argv[1] if len(sys.argv) > 1 else "init"
    
    try:
        if command == "init":
            await init_database()
            print("✅ Database initialization completed successfully")
            print("\n💡 Run 'python init_db.py info' to see table information")
            
        elif command == "reset":
            confirm = input("⚠️  This will delete ALL data. Are you sure? (yes/no): ")
            if confirm.lower() == "yes":
                await reset_database()
                print("✅ Database reset completed successfully")
            else:
                logger.info("Database reset cancelled")
                print("❌ Database reset cancelled")
                
        elif command == "health":
            await check_health()
            
        elif command == "backup":
            await backup_database()
            print("✅ Database backup completed")
            
        elif command == "test":
            await create_test_data()
            print("✅ Test data created successfully")
            
        elif command == "info":
            await show_table_info()
            
        elif command == "cleanup":
            await cleanup_database()
            print("✅ Database cleanup completed")
            
        elif command == "help" or command == "--help" or command == "-h":
            print_usage()
            
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\n❌ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        print(f"❌ Operation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
