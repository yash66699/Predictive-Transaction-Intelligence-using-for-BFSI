# crud.py - Database CRUD operations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, desc, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid

from app.models import (
    User, Transaction, FraudAlert, ChatHistory, UserSettings, 
    FileUpload, RuleEngine, ModelMetrics, SystemLog
)
from app.schemas import (
    UserCreate, TransactionCreate, FraudAlertCreate, 
    AlertStatus, UserSettings as UserSettingsSchema,
    DashboardStats, TransactionStats, AlertStats, ModelPerformance
)

# Configure logging
logger = logging.getLogger(__name__)

# User CRUD operations
async def get_user_by_uid(db: AsyncSession, firebase_uid: str) -> Optional[User]:
    """Get user by Firebase UID"""
    try:
        result = await db.execute(
            select(User).filter(User.firebase_uid == firebase_uid)
        )
        return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting user by UID: {e}")
        raise

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    try:
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        raise

async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create new user"""
    try:
        user = User(
            firebase_uid=user_data.firebase_uid,
            email=user_data.email,
            full_name=getattr(user_data, 'full_name', None),
            phone_number=getattr(user_data, 'phone_number', None)
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        
        # Create default user settings
        await create_user_settings(db, user.id)
        
        return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await db.rollback()
        raise

async def get_or_create_user(db: AsyncSession, firebase_user: Dict[str, Any]) -> User:
    """Get existing user or create new one"""
    try:
        user = await get_user_by_uid(db, firebase_user["uid"])
        if not user:
            user_data = UserCreate(
                firebase_uid=firebase_user["uid"],
                email=firebase_user.get("email", ""),
                full_name=firebase_user.get("name"),
                phone_number=None
            )
            user = await create_user(db, user_data)
            logger.info(f"Created new user with ID: {user.id}")
        return user
    except Exception as e:
        logger.error(f"Error getting or creating user: {e}")
        raise

# Transaction CRUD operations
async def create_transaction(db: AsyncSession, user_id: int, transaction_data: TransactionCreate) -> Transaction:
    """Create new transaction"""
    try:
        transaction = Transaction(
            transaction_id=transaction_data.transaction_id,
            user_id=user_id,
            transaction_amount=transaction_data.transaction_amount,
            kyc_verified=transaction_data.kyc_verified.value,
            account_age_days=transaction_data.account_age_days,
            channel=transaction_data.channel.value,
            timestamp=transaction_data.timestamp,
            customer_segment=getattr(transaction_data, 'customer_segment', 'Retail'),
            transaction_type=getattr(transaction_data, 'transaction_type', 'Purchase')
        )
        db.add(transaction)
        await db.flush()
        await db.refresh(transaction)
        return transaction
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        await db.rollback()
        raise

async def update_transaction_prediction(db: AsyncSession, transaction_id: str, prediction_data: Dict[str, Any]) -> bool:
    """Update transaction with prediction results"""
    try:
        stmt = (
            update(Transaction)
            .where(Transaction.transaction_id == transaction_id)
            .values(**prediction_data)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating transaction prediction: {e}")
        await db.rollback()
        raise

async def get_transactions_for_user(db: AsyncSession, user_id: int, limit: int = 50, offset: int = 0) -> List[Transaction]:
    """Get transactions for a user with pagination"""
    try:
        result = await db.execute(
            select(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting transactions for user: {e}")
        raise

async def get_transaction_by_id(db: AsyncSession, transaction_id: str) -> Optional[Transaction]:
    """Get transaction by transaction ID"""
    try:
        result = await db.execute(
            select(Transaction).filter(Transaction.transaction_id == transaction_id)
        )
        return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting transaction by ID: {e}")
        raise

async def get_user_avg_transaction_amount(db: AsyncSession, user_id: int, days: int = 30) -> float:
    """Get user's average transaction amount"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(func.avg(Transaction.transaction_amount))
            .filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= start_date
                )
            )
        )
        avg_amount = result.scalar()
        return float(avg_amount) if avg_amount else 1000.0
    except Exception as e:
        logger.error(f"Error getting user average transaction amount: {e}")
        return 1000.0

# Fraud Alert CRUD operations
async def create_fraud_alert(db: AsyncSession, alert_data: FraudAlertCreate) -> FraudAlert:
    """Create fraud alert"""
    try:
        alert = FraudAlert(
            transaction_id=alert_data.transaction_id,
            user_id=alert_data.user_id,
            risk_score=alert_data.risk_score,
            reason=alert_data.reason,
            rule_triggered=alert_data.rule_triggered,
            alert_type=alert_data.alert_type,
            severity=getattr(alert_data, 'severity', 'medium'),
            llm_explanation=getattr(alert_data, 'llm_explanation', None)
        )
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        return alert
    except Exception as e:
        logger.error(f"Error creating fraud alert: {e}")
        await db.rollback()
        raise

async def get_fraud_alerts_for_user(db: AsyncSession, user_id: int, limit: int = 20, 
                                  offset: int = 0, status: Optional[AlertStatus] = None) -> List[FraudAlert]:
    """Get fraud alerts for a user"""
    try:
        query = select(FraudAlert).filter(FraudAlert.user_id == user_id)
        
        if status:
            query = query.filter(FraudAlert.status == status.value)
        
        query = query.order_by(desc(FraudAlert.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting fraud alerts for user: {e}")
        raise

async def update_alert_status(db: AsyncSession, alert_id: int, status: str, reviewed_by: str) -> bool:
    """Update fraud alert status"""
    try:
        stmt = (
            update(FraudAlert)
            .where(FraudAlert.alert_id == alert_id)
            .values(
                status=status,
                reviewed_by=reviewed_by,
                reviewed_at=datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating alert status: {e}")
        await db.rollback()
        raise

# Chat CRUD operations
async def save_chat_message(db: AsyncSession, user_id: int, message: str, response: str, 
                          role: str, context: Optional[Dict] = None, confidence: Optional[float] = None) -> None:
    """Save chat message"""
    try:
        chat_msg = ChatHistory(
            user_id=user_id,
            message=message,
            response=response,
            role=role,
            context=context,
            confidence=confidence
        )
        db.add(chat_msg)
        await db.commit()
    except Exception as e:
        logger.error(f"Error saving chat message: {e}")
        await db.rollback()
        raise

async def get_chat_history(db: AsyncSession, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get chat history for a user"""
    try:
        result = await db.execute(
            select(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .order_by(desc(ChatHistory.timestamp))
            .limit(limit)
        )
        
        history = []
        for chat in result.scalars().all():
            history.append({
                "id": chat.id,
                "message": chat.message,
                "response": chat.response,
                "role": chat.role,
                "context": chat.context,
                "confidence": chat.confidence,
                "timestamp": chat.timestamp
            })
        return history
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise

# User Settings CRUD operations
async def create_user_settings(db: AsyncSession, user_id: int) -> UserSettings:
    """Create default user settings"""
    try:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
        return settings
    except Exception as e:
        logger.error(f"Error creating user settings: {e}")
        await db.rollback()
        raise

async def get_user_settings(db: AsyncSession, user_id: int) -> Optional[UserSettings]:
    """Get user settings"""
    try:
        result = await db.execute(
            select(UserSettings).filter(UserSettings.user_id == user_id)
        )
        return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise

async def update_user_settings(db: AsyncSession, user_id: int, settings_data: UserSettingsSchema) -> UserSettings:
    """Update user settings"""
    try:
        stmt = (
            update(UserSettings)
            .where(UserSettings.user_id == user_id)
            .values(
                notifications_enabled=settings_data.notifications_enabled,
                email_alerts=settings_data.email_alerts,
                sms_alerts=settings_data.sms_alerts,
                alert_threshold=settings_data.alert_threshold,
                preferred_language=settings_data.preferred_language
            )
        )
        await db.execute(stmt)
        await db.commit()
        
        # Return updated settings
        return await get_user_settings(db, user_id)
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        await db.rollback()
        raise

# File Upload CRUD operations
async def create_file_upload_record(db: AsyncSession, user_id: int, file_name: str, 
                                  file_size: int, file_type: str) -> str:
    """Create file upload record"""
    try:
        upload_id = str(uuid.uuid4())
        file_upload = FileUpload(
            user_id=user_id,
            upload_id=upload_id,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type
        )
        db.add(file_upload)
        await db.flush()
        return upload_id
    except Exception as e:
        logger.error(f"Error creating file upload record: {e}")
        await db.rollback()
        raise

async def update_file_upload_stats(db: AsyncSession, upload_id: str, total_rows: int, 
                                 processed_rows: int, fraud_count: int, error_count: int, 
                                 status: str = "completed") -> bool:
    """Update file upload statistics"""
    try:
        stmt = (
            update(FileUpload)
            .where(FileUpload.upload_id == upload_id)
            .values(
                total_rows=total_rows,
                processed_rows=processed_rows,
                fraud_count=fraud_count,
                error_count=error_count,
                status=status
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating file upload stats: {e}")
        await db.rollback()
        raise

# Analytics CRUD operations
async def get_user_analytics(db: AsyncSession, user_id: int, days: int = 30) -> Dict[str, Any]:
    """Get user analytics data"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Transaction statistics
        txn_result = await db.execute(
            select(
                func.count(Transaction.id).label('total'),
                func.count(Transaction.id).filter(Transaction.is_fraud == True).label('fraud_count'),
                func.sum(Transaction.transaction_amount).label('total_amount'),
                func.avg(Transaction.transaction_amount).label('avg_amount'),
                func.avg(Transaction.fraud_probability).label('avg_fraud_prob')
            )
            .filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= start_date
                )
            )
        )
        txn_stats = txn_result.fetchone()
        
        # Alert statistics
        alert_result = await db.execute(
            select(
                func.count(FraudAlert.alert_id).label('total_alerts'),
                func.count(FraudAlert.alert_id).filter(FraudAlert.status == 'pending').label('pending_alerts'),
                func.avg(FraudAlert.risk_score).label('avg_risk_score')
            )
            .filter(
                and_(
                    FraudAlert.user_id == user_id,
                    FraudAlert.created_at >= start_date
                )
            )
        )
        alert_stats = alert_result.fetchone()
        
        return {
            "transaction_stats": {
                "total_transactions": txn_stats.total or 0,
                "fraud_count": txn_stats.fraud_count or 0,
                "fraud_rate": (txn_stats.fraud_count / txn_stats.total * 100) if txn_stats.total else 0,
                "total_amount": float(txn_stats.total_amount or 0),
                "avg_amount": float(txn_stats.avg_amount or 0),
                "avg_fraud_probability": float(txn_stats.avg_fraud_prob or 0)
            },
            "alert_stats": {
                "total_alerts": alert_stats.total_alerts or 0,
                "pending_alerts": alert_stats.pending_alerts or 0,
                "avg_risk_score": float(alert_stats.avg_risk_score or 0)
            },
            "period_days": days
        }
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise

async def get_dashboard_stats(db: AsyncSession, user_id: int, days: int = 30) -> DashboardStats:
    """Get dashboard statistics"""
    try:
        # Get user analytics
        user_analytics = await get_user_analytics(db, user_id, days)
        
        # Get recent alerts
        recent_alerts_result = await db.execute(
            select(FraudAlert)
            .filter(FraudAlert.user_id == user_id)
            .order_by(desc(FraudAlert.created_at))
            .limit(5)
        )
        recent_alerts = recent_alerts_result.scalars().all()
        
        # Create dashboard stats
        return DashboardStats(
            user_stats={"user_id": user_id, "days": days},
            transaction_stats=TransactionStats(**user_analytics["transaction_stats"], date_range={"days": days}),
            alert_stats=AlertStats(**user_analytics["alert_stats"]),
            model_performance=ModelPerformance(
                accuracy=0.95,
                precision=0.92,
                recall=0.88,
                f1_score=0.90,
                total_predictions=user_analytics["transaction_stats"]["total_transactions"],
                last_updated=datetime.utcnow()
            ),
            recent_alerts=recent_alerts,
            top_risk_factors=["High amount", "Unverified KYC", "Odd hours", "New account"]
        )
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise

# ... (keep all existing code above, just update the system log functions)

# System log operations
async def create_system_log(db: AsyncSession, level: str, message: str, module: str = None, 
                          user_id: int = None, transaction_id: str = None, log_metadata: Dict = None) -> None:
    """Create system log entry"""
    try:
        log = SystemLog(
            level=level,
            message=message,
            module=module,
            user_id=user_id,
            transaction_id=transaction_id,
            log_metadata=log_metadata  # Updated field name
        )
        db.add(log)
        await db.commit()
    except Exception as e:
        logger.error(f"Error creating system log: {e}")
        await db.rollback()

# ... (keep all existing code below)


# Rule engine operations
async def get_active_rules(db: AsyncSession) -> List[RuleEngine]:
    """Get all active rules"""
    try:
        result = await db.execute(
            select(RuleEngine)
            .filter(RuleEngine.is_active == True)
            .order_by(RuleEngine.priority)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting active rules: {e}")
        raise

async def update_rule_trigger_count(db: AsyncSession, rule_id: int) -> None:
    """Update rule trigger count"""
    try:
        stmt = (
            update(RuleEngine)
            .where(RuleEngine.rule_id == rule_id)
            .values(
                trigger_count=RuleEngine.trigger_count + 1,
                last_triggered=datetime.utcnow()
            )
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        logger.error(f"Error updating rule trigger count: {e}")
        await db.rollback()
