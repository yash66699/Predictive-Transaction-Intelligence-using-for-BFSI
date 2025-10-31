# main.py - FastAPI application with all endpoints
import torch
import joblib
import uuid
import time
import io
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status, Header, Query, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import logging
from sqlalchemy.ext.asyncio import AsyncSession


# Import app modules
from app.firebase import verify_token
from app.database import connect_db, disconnect_db, get_db_session, check_db_health
from app.schemas import (
    UserCreate, User, UserUpdate, TransactionCreate, TransactionPredict, TransactionResponse,
    PredictionResult, FraudAlert, FraudAlertCreate, DashboardStats,
    HealthCheck, AlertStatus, BulkUploadResult, ChatMessage, ChatResponse,
    UserSettings, FileUploadResponse, APIResponse
)
from app.crud import (
    get_or_create_user, create_transaction, update_transaction_prediction,
    get_transactions_for_user, create_fraud_alert, get_fraud_alerts_for_user,
    get_user_avg_transaction_amount, get_transaction_by_id, update_alert_status,
    save_chat_message, get_chat_history, create_user_settings, get_user_settings,
    update_user_settings, create_file_upload_record, update_file_upload_stats,
    get_user_analytics, get_dashboard_stats
)
from app.services import get_fraud_detection_service, get_llm_service
from app.config import ALLOWED_ORIGINS, API_HOST, API_PORT, API_RELOAD, MAX_FILE_SIZE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Fraud Detection System API",
    description="AI-powered fraud detection with ML models, business rules, LLM explanations, and chat functionality",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        await connect_db()
        logger.info("Database connected successfully")
        
        # Test fraud detection service
        fraud_service = get_fraud_detection_service()
        health = fraud_service.get_system_health()
        logger.info(f"Fraud detection service initialized: {health}")
        
        # Test LLM service
        llm_service = get_llm_service()
        llm_health = await llm_service.health_check()
        logger.info(f"LLM service status: {llm_health}")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown"""
    try:
        await disconnect_db()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Application shutdown error: {e}")

# Authentication dependency
async def get_current_user(token: str = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from Firebase token"""
    try:
        user_info = await verify_token(token.credentials)
        logger.info(f"Token verified for user: {user_info['uid']}")
        return user_info
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Health check endpoints
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check database
        db_health = await check_db_health()
        
        # Check fraud detection service
        fraud_service = get_fraud_detection_service()
        ml_health = fraud_service.get_system_health()
        
        # Check LLM service
        llm_service = get_llm_service()
        llm_health = await llm_service.health_check()
        
        return HealthCheck(
            status="healthy" if db_health["status"] == "healthy" else "degraded",
            database=db_health["status"],
            model_loaded=ml_health["ml_service"]["model_loaded"],
            llm_available=llm_health["ollama_available"],
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime="0 days"  # Calculate actual uptime if needed
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service health check failed")

# User management endpoints
@app.get("/me", response_model=User)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current user profile"""
    try:
        user = await get_or_create_user(db, current_user)
        return user
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user profile")

@app.put("/me", response_model=User)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update current user profile"""
    try:
        user = await get_or_create_user(db, current_user)
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.phone_number is not None:
            user.phone_number = user_update.phone_number
        
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user profile")

@app.get("/me/settings", response_model=UserSettings)
async def get_user_settings_endpoint(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user settings"""
    try:
        user = await get_or_create_user(db, current_user)
        settings = await get_user_settings(db, user.id)
        if not settings:
            settings = await create_user_settings(db, user.id)
        return settings
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user settings")

@app.put("/me/settings", response_model=UserSettings)
async def update_user_settings_endpoint(
    settings_update: UserSettings,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update user settings"""
    try:
        user = await get_or_create_user(db, current_user)
        settings = await update_user_settings(db, user.id, settings_update)
        return settings
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user settings")

# Fraud prediction endpoints
@app.post("/predict", response_model=PredictionResult)
async def predict_fraud(
    transaction_data: TransactionPredict,
    include_explanation: bool = Query(True, description="Include LLM explanation"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Predict fraud for a transaction with optional LLM explanation"""
    try:
        user = await get_or_create_user(db, current_user)
        
        # Get user average transaction amount
        user_avg_amount = await get_user_avg_transaction_amount(db, user.id)
        
        # Get fraud prediction service
        fraud_service = get_fraud_detection_service()
        
        # Make prediction with or without explanation
        if include_explanation:
            prediction_result = await fraud_service.predict_fraud_with_explanation(
                transaction_data.dict(), user_avg_amount
            )
        else:
            prediction_result = fraud_service.predict_fraud(
                transaction_data.dict(), user_avg_amount
            )
        
        # Save transaction to database
        transaction_create = TransactionCreate(
            transaction_id=prediction_result.transaction_id,
            **transaction_data.dict()
        )
        
        saved_transaction = await create_transaction(db, user.id, transaction_create)
        
        # Update transaction with prediction results
        await update_transaction_prediction(db, prediction_result.transaction_id, {
            "fraud_probability": prediction_result.fraud_probability,
            "is_fraud": prediction_result.is_fraud,
            "risk_score": prediction_result.risk_score,
            "model_version": prediction_result.model_version,
            "rules_triggered": prediction_result.rules_triggered,
            "reason": prediction_result.reason,
            "llm_explanation": prediction_result.llm_explanation
        })
        
        # Create fraud alert if needed
        if prediction_result.is_fraud:
            alert_data = FraudAlertCreate(
                transaction_id=prediction_result.transaction_id,
                user_id=user.id,
                risk_score=prediction_result.risk_score,
                reason=prediction_result.reason,
                rule_triggered=",".join(prediction_result.rules_triggered),
                llm_explanation=prediction_result.llm_explanation,
                severity="high" if prediction_result.risk_score > 0.8 else "medium"
            )
            await create_fraud_alert(db, alert_data)
        
        logger.info(f"Fraud prediction completed for user {user.id}")
        return prediction_result
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process fraud prediction")

# Transaction endpoints
@app.get("/transactions", response_model=List[TransactionResponse])
async def get_transaction_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's transaction history with pagination"""
    try:
        user = await get_or_create_user(db, current_user)
        transactions = await get_transactions_for_user(db, user.id, limit=limit, offset=offset)
        return transactions
        
    except Exception as e:
        logger.error(f"Error getting transaction history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transaction history")

@app.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_details(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get specific transaction details"""
    try:
        user = await get_or_create_user(db, current_user)
        transaction = await get_transaction_by_id(db, transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Verify transaction belongs to user
        if transaction.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transaction details")

# Fraud alerts endpoints
@app.get("/alerts", response_model=List[FraudAlert])
async def get_fraud_alerts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[AlertStatus] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's fraud alerts with pagination and filtering"""
    try:
        user = await get_or_create_user(db, current_user)
        alerts = await get_fraud_alerts_for_user(db, user.id, limit=limit, offset=offset, status=status)
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting fraud alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fraud alerts")

@app.put("/alerts/{alert_id}/status")
async def update_fraud_alert_status(
    alert_id: int,
    new_status: AlertStatus = Body(..., embed=True),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update fraud alert status"""
    try:
        user = await get_or_create_user(db, current_user)
        
        # Update alert status
        updated = await update_alert_status(db, alert_id, new_status.value, user.email)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": f"Alert status updated to {new_status.value}", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert status")

# File upload endpoints
@app.post("/upload/csv", response_model=FileUploadResponse)
async def upload_csv_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Upload and process CSV file for bulk fraud detection"""
    try:
        # Validate file
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_FILE_SIZE/1024/1024}MB limit")
        
        user = await get_or_create_user(db, current_user)
        
        # Create upload record
        upload_id = await create_file_upload_record(db, user.id, file.filename, file.size or 0, "csv")
        
        # Read and validate CSV
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Validate required columns
        required_cols = ['transaction_amount', 'kyc_verified', 'account_age_days', 'channel', 'timestamp']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_cols}"
            )
        
        # Process transactions
        fraud_service = get_fraud_detection_service()
        user_avg_amount = await get_user_avg_transaction_amount(db, user.id)
        
        results = []
        fraud_count = 0
        error_count = 0
        errors = []
        
        start_time = time.time()
        
        for index, row in df.iterrows():
            try:
                transaction_data = {
                    'transaction_amount': float(row['transaction_amount']),
                    'kyc_verified': row['kyc_verified'],
                    'account_age_days': int(row['account_age_days']),
                    'channel': row['channel'],
                    'timestamp': row['timestamp'],
                    'customer_segment': row.get('customer_segment', 'Retail'),
                    'transaction_type': row.get('transaction_type', 'Purchase')
                }
                
                # Make prediction
                prediction = await fraud_service.predict_fraud_with_explanation(
                    transaction_data, user_avg_amount
                )
                
                # Save to database
                transaction_create = TransactionCreate(
                    transaction_id=prediction.transaction_id,
                    **{k: v for k, v in transaction_data.items() if k != 'customer_segment' and k != 'transaction_type'}
                )
                await create_transaction(db, user.id, transaction_create)
                await update_transaction_prediction(db, prediction.transaction_id, prediction.dict())
                
                # Create alert if fraud
                if prediction.is_fraud:
                    fraud_count += 1
                    alert_data = FraudAlertCreate(
                        transaction_id=prediction.transaction_id,
                        user_id=user.id,
                        risk_score=prediction.risk_score,
                        reason=prediction.reason,
                        rule_triggered=",".join(prediction.rules_triggered),
                        llm_explanation=prediction.llm_explanation
                    )
                    await create_fraud_alert(db, alert_data)
                
                results.append(prediction)
                
            except Exception as row_error:
                error_count += 1
                errors.append(f"Row {index + 2}: {str(row_error)}")
                logger.error(f"Error processing CSV row {index + 2}: {row_error}")
        
        processing_time = time.time() - start_time
        
        # Update upload statistics
        await update_file_upload_stats(
            db, upload_id, len(df), len(results), fraud_count, error_count, "completed"
        )
        
        return FileUploadResponse(
            message=f"Successfully processed {len(results)} transactions from CSV",
            upload_id=upload_id,
            file_name=file.filename,
            file_size=file.size or 0,
            total_rows=len(df),
            processed_rows=len(results),
            fraud_count=fraud_count,
            legitimate_count=len(results) - fraud_count,
            error_count=error_count,
            errors=errors[:10]  # Return first 10 errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process CSV file")

# Chat endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat_with_llm(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Chat with LLM assistant about fraud detection"""
    try:
        user = await get_or_create_user(db, current_user)
        
        # Get user context for better responses
        user_context = await get_user_analytics(db, user.id)
        
        # Get LLM response
        fraud_service = get_fraud_detection_service()
        response = await fraud_service.chat_with_llm(
            message.message, user.id, user_context
        )
        
        # Save chat messages
        await save_chat_message(db, user.id, message.message, response, "user", message.context)
        await save_chat_message(db, user.id, response, response, "assistant", None, 0.8)
        
        return ChatResponse(
            response=response,
            confidence=0.8,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@app.get("/chat/history")
async def get_chat_history_endpoint(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get chat history for current user"""
    try:
        user = await get_or_create_user(db, current_user)
        history = await get_chat_history(db, user.id, limit=limit)
        return history
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

# Analytics endpoints
@app.get("/analytics/dashboard", response_model=DashboardStats)
async def get_dashboard_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get dashboard analytics for user"""
    try:
        user = await get_or_create_user(db, current_user)
        stats = await get_dashboard_stats(db, user.id, days)
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@app.get("/analytics/user")
async def get_user_analytics_endpoint(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user analytics data"""
    try:
        user = await get_or_create_user(db, current_user)
        analytics = await get_user_analytics(db, user.id, days)
        return analytics
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

# System endpoints
@app.get("/system/health/detailed")
async def get_detailed_health_check(current_user: dict = Depends(get_current_user)):
    """Detailed health check with system metrics"""
    try:
        db_health = await check_db_health()
        fraud_service = get_fraud_detection_service()
        ml_health = fraud_service.get_system_health()
        llm_health = await get_llm_service().health_check()
        
        return {
            "database": db_health,
            "ml_service": ml_health,
            "llm_service": llm_health,
            "timestamp": datetime.utcnow(),
            "status": "healthy" if all([
                db_health["status"] == "healthy",
                ml_health["ml_service"]["model_loaded"],
                llm_health["ollama_available"]
            ]) else "degraded"
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    logger.error(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": str(exc), "timestamp": datetime.utcnow().isoformat()}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
    )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Fraud Detection System API with LLM Integration",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.utcnow(),
        "features": [
            "ML-powered fraud detection",
            "Business rules engine", 
            "LLM explanations via Llama 3",
            "Chat functionality",
            "CSV bulk processing",
            "Real-time analytics"
        ],
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=API_RELOAD)
