# models.py - SQLAlchemy ORM Models
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    """User model for Firebase authenticated users"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    fraud_alerts = relationship("FraudAlert", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    user_settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    file_uploads = relationship("FileUpload", back_populates="user", cascade="all, delete-orphan")

class Transaction(Base):
    """Transaction model for storing transaction data and predictions"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Transaction features
    transaction_amount = Column(Float, nullable=False)
    kyc_verified = Column(String, nullable=False)
    account_age_days = Column(Integer, nullable=False)
    channel = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # ML prediction results
    fraud_probability = Column(Float, nullable=True)
    is_fraud = Column(Boolean, nullable=True)
    risk_score = Column(Float, nullable=True)
    model_version = Column(String, default="v1.0")
    rules_triggered = Column(ARRAY(String), nullable=True)
    reason = Column(Text, nullable=True)
    llm_explanation = Column(Text, nullable=True)
    
    # Additional features
    customer_segment = Column(String, nullable=True)
    transaction_type = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    fraud_alerts = relationship("FraudAlert", back_populates="transaction", cascade="all, delete-orphan")

class FraudAlert(Base):
    """Fraud alert model for storing flagged transactions"""
    __tablename__ = "fraud_alerts"
    
    alert_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Alert details
    risk_score = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    rule_triggered = Column(String, nullable=True)
    alert_type = Column(String, default="fraud_detection")
    severity = Column(String, default="medium")
    
    # Status
    status = Column(String, default="pending")
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # LLM explanation
    llm_explanation = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="fraud_alerts")
    transaction = relationship("Transaction", back_populates="fraud_alerts")

class ChatHistory(Base):
    """Chat history model for storing LLM conversations"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    context = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_history")

class UserSettings(Base):
    """User settings model for personalized preferences"""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    notifications_enabled = Column(Boolean, default=True)
    email_alerts = Column(Boolean, default=True)
    sms_alerts = Column(Boolean, default=False)
    alert_threshold = Column(Float, default=0.7)
    preferred_language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_settings")

class FileUpload(Base):
    """File upload model for tracking CSV uploads"""
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(String, unique=True, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    total_rows = Column(Integer, nullable=True)
    processed_rows = Column(Integer, nullable=True)
    fraud_count = Column(Integer, nullable=True)
    error_count = Column(Integer, nullable=True)
    status = Column(String, default="processing")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="file_uploads")

class RuleEngine(Base):
    """Model for storing dynamic fraud detection rules"""
    __tablename__ = "rule_engine"
    
    rule_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_name = Column(String, unique=True, nullable=False)
    rule_description = Column(Text, nullable=False)
    rule_logic = Column(Text, nullable=False)  # JSON or code for rule logic
    
    # Rule settings
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    threshold = Column(Float, nullable=True)
    
    # Metadata
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)

class ModelMetrics(Base):
    """Model for storing ML model performance metrics"""
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_version = Column(String, nullable=False)
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    auc_roc = Column(Float, nullable=True)
    
    # Additional metrics
    total_predictions = Column(Integer, default=0)
    fraud_detected = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    
    # Metadata
    evaluation_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemLog(Base):
    """System log model for tracking system events"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    level = Column(String, nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    module = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    transaction_id = Column(String, nullable=True)
    # Changed 'metadata' to 'log_metadata' to avoid conflict with SQLAlchemy's reserved 'metadata'
    log_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
