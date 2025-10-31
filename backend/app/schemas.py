# schemas.py - Pydantic models for request/response validation
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

# Enums for validation
class ChannelType(str, Enum):
    domestic = "domestic"
    international = "international"
    online = "online"
    atm = "atm"
    mobile = "mobile"

class KYCStatus(str, Enum):
    yes = "Yes"
    no = "No"
    pending = "Pending"

class AlertStatus(str, Enum):
    pending = "pending"
    reviewed = "reviewed"
    resolved = "resolved"
    false_positive = "false_positive"

class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    firebase_uid: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class User(UserBase):
    id: int
    firebase_uid: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    transaction_amount: float = Field(..., gt=0, description="Transaction amount must be positive")
    kyc_verified: KYCStatus
    account_age_days: int = Field(..., ge=0, description="Account age must be non-negative")
    channel: ChannelType
    timestamp: datetime
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            v_aware = v.replace(tzinfo=timezone.utc)
        else:
            v_aware = v.astimezone(timezone.utc)
        now_utc = datetime.now(timezone.utc)
        
        if v_aware > now_utc:
            raise ValueError("Timestamp cannot be in the future.")
        return v

class TransactionCreate(TransactionBase):
    transaction_id: str = Field(..., min_length=1, max_length=100)

class TransactionPredict(TransactionBase):
    """Schema for prediction requests (no transaction_id required)"""
    customer_segment: Optional[str] = "Retail"
    transaction_type: Optional[str] = "Purchase"

class TransactionResponse(TransactionBase):
    id: int
    transaction_id: str
    user_id: int
    fraud_probability: Optional[float] = None
    is_fraud: Optional[bool] = None
    risk_score: Optional[float] = None
    model_version: Optional[str] = None
    rules_triggered: Optional[List[str]] = []
    reason: Optional[str] = None
    llm_explanation: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PredictionResult(BaseModel):
    """Schema for ML prediction results"""
    transaction_id: str
    is_fraud: bool
    fraud_probability: float
    risk_score: float
    prediction_confidence: float
    model_version: str
    rules_triggered: List[str] = []
    reason: str
    llm_explanation: Optional[str] = None
    timestamp: datetime

# Fraud Alert schemas
class FraudAlertBase(BaseModel):
    risk_score: float = Field(..., ge=0, le=1, description="Risk score between 0 and 1")
    reason: str = Field(..., min_length=1, max_length=1000)
    rule_triggered: Optional[str] = None
    alert_type: str = "fraud_detection"
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")

class FraudAlertCreate(FraudAlertBase):
    transaction_id: str
    user_id: int
    llm_explanation: Optional[str] = None

class FraudAlert(FraudAlertBase):
    alert_id: int
    transaction_id: str
    user_id: int
    status: AlertStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    llm_explanation: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Chat schemas
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    confidence: Optional[float] = None
    timestamp: datetime

class ChatHistory(BaseModel):
    id: int
    user_id: int
    message: str
    response: str
    role: ChatRole
    timestamp: datetime
    
    class Config:
        from_attributes = True

# File Upload schemas
class BulkUploadResult(BaseModel):
    total_processed: int
    fraud_detected: int
    legitimate_transactions: int
    errors: List[str] = []
    processing_time: float
    upload_id: str

class FileUploadResponse(BaseModel):
    message: str
    upload_id: str
    file_name: str
    file_size: int
    total_rows: int
    processed_rows: int
    fraud_count: int
    legitimate_count: int
    error_count: int
    errors: List[str] = []

# Rule Engine schemas
class RuleEngineBase(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=100)
    rule_description: str = Field(..., min_length=1, max_length=500)
    rule_logic: str = Field(..., min_length=1)
    is_active: bool = True
    priority: int = Field(default=1, ge=1, le=10)
    threshold: Optional[float] = None

class RuleEngineCreate(RuleEngineBase):
    created_by: Optional[str] = None

class RuleEngine(RuleEngineBase):
    rule_id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    class Config:
        from_attributes = True

# Analytics and reporting schemas
class TransactionStats(BaseModel):
    total_transactions: int
    fraud_count: int
    fraud_rate: float
    total_amount: float
    avg_amount: float
    date_range: Dict[str, Any]

class AlertStats(BaseModel):
    total_alerts: int
    pending_alerts: int
    resolved_alerts: int
    false_positives: int
    avg_risk_score: float

class ModelPerformance(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    total_predictions: int
    last_updated: datetime

class DashboardStats(BaseModel):
    user_stats: Dict[str, Any]
    transaction_stats: TransactionStats
    alert_stats: AlertStats
    model_performance: ModelPerformance
    recent_alerts: List[FraudAlert]
    top_risk_factors: List[str]

# Model performance schemas
class ModelMetricsBase(BaseModel):
    model_version: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None

class ModelMetrics(ModelMetricsBase):
    id: int
    total_predictions: int = 0
    fraud_detected: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    evaluation_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Health check schema
class HealthCheck(BaseModel):
    status: str
    database: str
    model_loaded: bool
    llm_available: bool
    timestamp: datetime
    version: str
    uptime: str

# User Settings schemas
class UserSettings(BaseModel):
    notifications_enabled: bool = True
    email_alerts: bool = True
    sms_alerts: bool = False
    alert_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    preferred_language: str = "en"

# Bulk operations schemas
class BulkTransactionCreate(BaseModel):
    transactions: List[TransactionCreate]

class BulkPredictionResult(BaseModel):
    results: List[PredictionResult]
    summary: Dict[str, Any]

# LLM related schemas
class LLMExplanationRequest(BaseModel):
    transaction_data: Dict[str, Any]
    prediction_result: Dict[str, Any]
    rules_triggered: List[str]

class LLMExplanationResponse(BaseModel):
    explanation: str
    confidence_score: float
    key_factors: List[str]

# API Response schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# Export schemas
class ExportRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field(default="csv", pattern="^(csv|xlsx|json|pdf)$")
    include_predictions: bool = True
    include_alerts: bool = True
    filters: Optional[Dict[str, Any]] = None
