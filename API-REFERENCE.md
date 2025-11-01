# 📡 Complete API Reference Guide
## Predictive Transaction Intelligence System

---

## 🔑 Authentication

All endpoints (except `/health` and `/docs`) require authentication.

### Get JWT Token (Login)

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1440
}
```

### Use Token in Requests

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/transactions
```

---

## 🔍 Core Endpoints

### 1️⃣ Transaction Prediction (PRIMARY)

#### Predict Single Transaction

```http
POST /predict?include_explanation=true
Content-Type: application/json
Authorization: Bearer <token>

Request Body:
{
  "transaction_amount": 75000.00,
  "kyc_verified": "Yes|No|Pending",
  "account_age_days": 5,
  "channel": "domestic|international|online|atm|mobile",
  "timestamp": "2025-11-01T15:30:00",
  "customer_segment": "Retail|Premium|Corporate",
  "transaction_type": "Purchase|Transfer|Withdrawal"
}

Response (200 OK):
{
  "transaction_id": "TXN-1730461800000",
  "is_fraud": true,
  "fraud_probability": 0.8547,
  "risk_score": 0.8213,
  "rules_triggered": [
    "high_amount_rule",
    "unverified_kyc_international",
    "new_account_high_amount",
    "odd_hours_rule"
  ],
  "reason": "High transaction amount ($75,000) combined with unverified KYC status for international channel and new account (5 days old)",
  "llm_explanation": "This transaction exhibits multiple fraud indicators. The combination of high amount, unverified KYC, international channel, new account age, and transaction timing at 3 AM suggests potential fraudulent activity. Recommend immediate verification with customer.",
  "model_version": "v1.0-hybrid-lstm-transformer",
  "processing_time_ms": 87,
  "timestamp": "2025-11-01T15:30:00"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `transaction_id` | string | Unique transaction identifier |
| `is_fraud` | boolean | Fraud prediction result |
| `fraud_probability` | float | 0-1 probability of fraud (ML model) |
| `risk_score` | float | 0-1 weighted risk score (70% ML + 30% rules) |
| `rules_triggered` | array | List of business rules that flagged transaction |
| `reason` | string | Human-readable reason for prediction |
| `llm_explanation` | string | LLM-generated detailed explanation |
| `model_version` | string | ML model version used |
| `processing_time_ms` | int | API response time in milliseconds |
| `timestamp` | string | ISO timestamp of prediction |

---

### 2️⃣ Transaction History

#### List All Transactions

```http
GET /transactions?limit=50&offset=0&filter=all&sort_by=created_at&sort_order=desc
Authorization: Bearer <token>

Query Parameters:
- limit: 1-100 (default: 50)
- offset: 0-N (default: 0, for pagination)
- filter: "all|fraud|legitimate" (default: all)
- sort_by: "created_at|amount|risk_score" (default: created_at)
- sort_order: "asc|desc" (default: desc)

Response (200 OK):
{
  "total": 150,
  "limit": 50,
  "offset": 0,
  "transactions": [
    {
      "transaction_id": "TXN-1730461800000",
      "user_id": "user-123",
      "amount": 75000.00,
      "kyc_verified": "No",
      "account_age_days": 5,
      "channel": "international",
      "is_fraud": true,
      "fraud_probability": 0.8547,
      "risk_score": 0.8213,
      "rules_triggered": ["high_amount_rule", "unverified_kyc_international"],
      "reason": "High amount unverified KYC international",
      "created_at": "2025-11-01T15:30:00",
      "updated_at": "2025-11-01T15:30:01"
    }
  ]
}
```

#### Get Single Transaction

```http
GET /transactions/{transaction_id}
Authorization: Bearer <token>

Response (200 OK):
{
  "transaction_id": "TXN-1730461800000",
  "user_id": "user-123",
  "amount": 75000.00,
  "kyc_verified": "No",
  "account_age_days": 5,
  "channel": "international",
  "timestamp": "2025-11-01T15:30:00",
  "is_fraud": true,
  "fraud_probability": 0.8547,
  "risk_score": 0.8213,
  "rules_triggered": ["high_amount_rule", "unverified_kyc_international"],
  "reason": "High amount unverified KYC international",
  "llm_explanation": "This transaction exhibits multiple fraud indicators...",
  "created_at": "2025-11-01T15:30:00",
  "updated_at": "2025-11-01T15:30:01"
}
```

---

### 3️⃣ Fraud Alerts

#### List Fraud Alerts

```http
GET /alerts?status=pending&severity=high&limit=50
Authorization: Bearer <token>

Query Parameters:
- status: "pending|reviewed|resolved" (optional)
- severity: "high|medium|low" (optional)
- limit: 1-100 (default: 50)

Response (200 OK):
{
  "total": 12,
  "alerts": [
    {
      "alert_id": "ALERT-1730461800000",
      "transaction_id": "TXN-1730461800000",
      "user_id": "user-123",
      "fraud_probability": 0.8547,
      "risk_score": 0.8213,
      "severity": "HIGH",
      "status": "pending",
      "notes": [],
      "created_at": "2025-11-01T15:30:00",
      "updated_at": "2025-11-01T15:30:00"
    }
  ]
}
```

#### Update Alert Status

```http
PUT /alerts/{alert_id}/status
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "new_status": "reviewed|resolved",
  "notes": "Customer verified transaction"
}

Response (200 OK):
{
  "alert_id": "ALERT-1730461800000",
  "status": "reviewed",
  "updated_at": "2025-11-01T15:35:00"
}
```

#### Add Alert Notes

```http
POST /alerts/{alert_id}/notes
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "note": "Contacted customer. Transaction approved."
}

Response (200 OK):
{
  "alert_id": "ALERT-1730461800000",
  "notes": ["Contacted customer. Transaction approved."],
  "updated_at": "2025-11-01T15:35:00"
}
```

---

### 4️⃣ Chat with AI Assistant

#### Send Message to LLM

```http
POST /chat
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "message": "What factors indicate fraud?",
  "context": {
    "total_transactions": 150,
    "fraud_count": 12,
    "recent_transactions": ["TXN-123", "TXN-124"]
  }
}

Response (200 OK):
{
  "message_id": "MSG-1730461800000",
  "user_message": "What factors indicate fraud?",
  "assistant_response": "Our fraud detection system evaluates multiple factors: 1. Transaction Amount - unusually high amounts; 2. KYC Status - unverified KYC with high-risk channels; 3. Account Age - new accounts with large transactions; 4. Transaction Timing - transactions during odd hours (midnight-6am); 5. Channel Type - international vs domestic transactions. These factors are weighted and combined with machine learning models for accurate predictions.",
  "model": "llama3",
  "confidence": 0.92,
  "processing_time_ms": 1240,
  "timestamp": "2025-11-01T15:30:00"
}
```

#### Chat History

```http
GET /chat/history?limit=50&offset=0
Authorization: Bearer <token>

Response (200 OK):
{
  "total": 12,
  "conversations": [
    {
      "message_id": "MSG-1730461800000",
      "user_message": "What factors indicate fraud?",
      "assistant_response": "Our fraud detection system evaluates...",
      "timestamp": "2025-11-01T15:30:00"
    }
  ]
}
```

---

### 5️⃣ Bulk CSV Upload

#### Upload CSV File

```http
POST /upload/csv
Authorization: Bearer <token>
Content-Type: multipart/form-data

Request Body:
file: <CSV file>

CSV Format (required columns):
transaction_amount,kyc_verified,account_age_days,channel,timestamp,customer_segment,transaction_type
75000,No,5,international,2025-11-01T15:30:00,Retail,Purchase
50000,Yes,100,domestic,2025-11-01T16:00:00,Premium,Transfer

Response (200 OK):
{
  "upload_id": "UPLOAD-1730461800000",
  "filename": "transactions.csv",
  "processed_rows": 1000,
  "fraud_count": 45,
  "legitimate_count": 955,
  "processing_time_ms": 4230,
  "results_url": "/uploads/UPLOAD-1730461800000/results.json"
}
```

#### Download Upload Results

```http
GET /uploads/{upload_id}/results
Authorization: Bearer <token>

Response (200 OK):
{
  "upload_id": "UPLOAD-1730461800000",
  "total_rows": 1000,
  "fraud_count": 45,
  "fraud_percentage": 4.5,
  "high_risk_count": 120,
  "timestamp": "2025-11-01T15:30:00",
  "details": [
    {
      "row": 1,
      "transaction_amount": 75000,
      "is_fraud": true,
      "risk_score": 0.82,
      "status": "fraud"
    }
  ]
}
```

---

### 6️⃣ Model Performance

#### Get Model Metrics

```http
GET /model/performance
Authorization: Bearer <token>

Response (200 OK):
{
  "model_version": "v1.0-hybrid-lstm-transformer",
  "last_trained": "2025-10-15T10:00:00",
  "metrics": {
    "accuracy": 0.954,
    "precision": 0.923,
    "recall": 0.857,
    "f1_score": 0.889,
    "roc_auc": 0.9876
  },
  "confusion_matrix": {
    "true_negatives": 105,
    "false_positives": 3,
    "false_negatives": 5,
    "true_positives": 30
  },
  "inference_statistics": {
    "avg_inference_time_ms": 87,
    "min_inference_time_ms": 45,
    "max_inference_time_ms": 234,
    "total_predictions": 10567
  }
}
```

#### Get Model Training History

```http
GET /model/training-history?limit=10
Authorization: Bearer <token>

Response (200 OK):
{
  "training_runs": [
    {
      "run_id": "RUN-20251015-100000",
      "model_version": "v1.0-hybrid-lstm-transformer",
      "training_date": "2025-10-15T10:00:00",
      "metrics": {
        "accuracy": 0.954,
        "f1_score": 0.889
      },
      "dataset_size": 50000,
      "training_time_minutes": 45
    }
  ]
}
```

---

### 7️⃣ Dashboard Analytics

#### Get Dashboard Statistics

```http
GET /analytics/dashboard?days=30
Authorization: Bearer <token>

Query Parameters:
- days: 1-365 (default: 30)

Response (200 OK):
{
  "period": {
    "start_date": "2025-10-02T00:00:00",
    "end_date": "2025-11-01T23:59:59",
    "days": 30
  },
  "statistics": {
    "total_transactions": 5432,
    "fraud_count": 234,
    "legitimate_count": 5198,
    "fraud_percentage": 4.31,
    "avg_transaction_amount": 45230.50,
    "total_fraud_amount": 12450000.00,
    "unique_users": 892
  },
  "trends": {
    "daily_transactions": [245, 267, 189, ...],
    "daily_fraud_count": [12, 15, 8, ...],
    "daily_fraud_rate": [4.9, 5.6, 4.2, ...]
  }
}
```

#### Get Top Fraud Patterns

```http
GET /analytics/fraud-patterns?limit=10
Authorization: Bearer <token>

Response (200 OK):
{
  "patterns": [
    {
      "rank": 1,
      "pattern": "high_amount + unverified_kyc + international",
      "occurrence_count": 89,
      "fraud_rate": 0.98,
      "avg_transaction_amount": 75000
    }
  ]
}
```

---

### 8️⃣ User Management

#### Create User

```http
POST /users
Content-Type: application/json

Request Body:
{
  "email": "user@example.com",
  "password": "secure_password_123",
  "name": "John Doe",
  "role": "analyst"
}

Response (201 Created):
{
  "user_id": "user-123",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "analyst",
  "created_at": "2025-11-01T15:30:00"
}
```

#### Update User Profile

```http
PUT /users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "name": "John Doe",
  "email": "newemail@example.com"
}

Response (200 OK):
{
  "user_id": "user-123",
  "email": "newemail@example.com",
  "name": "John Doe",
  "updated_at": "2025-11-01T15:35:00"
}
```

---

### 9️⃣ System Health

#### Health Check

```http
GET /health

Response (200 OK):
{
  "status": "healthy",
  "database": "connected",
  "ollama": "connected",
  "firebase": "connected",
  "timestamp": "2025-11-01T15:30:00",
  "uptime_seconds": 432000
}
```

#### Service Status

```http
GET /status

Response (200 OK):
{
  "api": {
    "status": "running",
    "version": "1.0.0"
  },
  "database": {
    "status": "connected",
    "response_time_ms": 5
  },
  "cache": {
    "status": "active",
    "size_mb": 256
  },
  "ollama": {
    "status": "connected",
    "model": "llama3",
    "response_time_ms": 1200
  }
}
```

---

## 🛠️ Error Responses

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Bad Request | Check request format/parameters |
| 401 | Unauthorized | Provide valid JWT token |
| 403 | Forbidden | Check user permissions |
| 404 | Not Found | Verify resource ID |
| 422 | Validation Error | Check required fields |
| 429 | Rate Limited | Wait before retrying |
| 500 | Server Error | Contact support |

### Error Response Format

```json
{
  "error": "validation_error",
  "message": "Transaction amount must be greater than 0",
  "status_code": 422,
  "details": {
    "field": "transaction_amount",
    "issue": "value_error.number.not_gt"
  }
}
```

---

## 📊 Rate Limiting

- **Tier 1 (Free)**: 100 requests/hour
- **Tier 2 (Pro)**: 10,000 requests/hour
- **Tier 3 (Enterprise)**: Unlimited

Headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1730465400
```

---

## 🔗 Webhooks (Optional)

Subscribe to events:

```http
POST /webhooks/subscribe
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["fraud_detected", "alert_resolved"],
  "headers": {
    "Authorization": "Bearer your-token"
  }
}
```

Webhook Payload:
```json
{
  "event": "fraud_detected",
  "timestamp": "2025-11-01T15:30:00",
  "data": {
    "transaction_id": "TXN-123",
    "is_fraud": true,
    "risk_score": 0.82
  }
}
```

---

## 📚 SDK Examples

### Python

```python
import requests

API_URL = "http://localhost:8000"
TOKEN = "your_jwt_token"

def predict_transaction(amount, kyc, age, channel):
    response = requests.post(
        f"{API_URL}/predict?include_explanation=true",
        json={
            "transaction_amount": amount,
            "kyc_verified": kyc,
            "account_age_days": age,
            "channel": channel,
            "timestamp": "2025-11-01T15:30:00"
        },
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    return response.json()

result = predict_transaction(75000, "No", 5, "international")
print(result)
```

### JavaScript/Node.js

```javascript
const API_URL = "http://localhost:8000";
const TOKEN = "your_jwt_token";

async function predictTransaction(amount, kyc, age, channel) {
  const response = await fetch(`${API_URL}/predict?include_explanation=true`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${TOKEN}`
    },
    body: JSON.stringify({
      transaction_amount: amount,
      kyc_verified: kyc,
      account_age_days: age,
      channel: channel,
      timestamp: new Date().toISOString()
    })
  });
  return await response.json();
}

predictTransaction(75000, "No", 5, "international").then(result => {
  console.log(result);
});
```

---

**For more information, visit the [Main README](README.md)**