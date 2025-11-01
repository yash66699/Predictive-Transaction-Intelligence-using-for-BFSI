# 📋 Installation & Setup Guide
## Predictive Transaction Intelligence System

---

## 🎯 Complete Step-by-Step Setup

### Phase 1: Prerequisites Installation

#### Step 1.1: Install Python 3.8+

**Windows:**
```bash
# Download from https://www.python.org/downloads/
# Run installer, check "Add Python to PATH"
python --version  # Verify installation
```

**macOS:**
```bash
brew install python@3.11
python3 --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-pip
python3 --version
```

#### Step 1.2: Install PostgreSQL 14+

**Windows:**
```bash
# Download from https://www.postgresql.org/download/windows/
# Run installer, remember the password for `postgres` user
psql --version
```

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
psql --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql-14 postgresql-contrib-14
sudo systemctl start postgresql
psql --version
```

#### Step 1.3: Install Git

```bash
# Windows: https://git-scm.com/download/win
# macOS: brew install git
# Linux: sudo apt-get install git
git --version
```

#### Step 1.4: Install Ollama (for LLM)

```bash
# Download from https://ollama.ai
# Run installer for your OS
ollama --version

# Pull Llama 3 model
ollama pull llama3
```

---

### Phase 2: Repository Setup

#### Step 2.1: Clone Repository

```bash
git clone https://github.com/yash66699/Predictive-Transaction-Intelligence-using-for-BFSI.git
cd Predictive-Transaction-Intelligence-using-for-BFSI
```

#### Step 2.2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 2.3: Install Python Dependencies

```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Phase 3: Database Setup

#### Step 3.1: Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# In PostgreSQL prompt:
CREATE DATABASE fraud_detection_db OWNER postgres;
CREATE USER fraud_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE fraud_detection_db TO fraud_user;
\q  # Exit
```

#### Step 3.2: Configure Environment Variables

```bash
# In backend/ directory, create .env file:
cp .env.example .env

# Edit .env with your values:
DATABASE_URL=postgresql://fraud_user:your_secure_password@localhost:5432/fraud_detection_db
FIREBASE_PROJECT_ID=your-firebase-project-id
OLLAMA_BASE_URL=http://localhost:11434
SECRET_KEY=your-super-secret-key-change-this
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

#### Step 3.3: Initialize Database Schema

```bash
python init_db.py
# Creates all tables and sample data
```

---

### Phase 4: Firebase Setup

#### Step 4.1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create Project"
3. Name: "fraud-detection-system"
4. Enable Google Analytics
5. Create Project

#### Step 4.2: Set Up Authentication

1. In Firebase Console → Authentication → Sign-in method
2. Enable: Email/Password
3. Enable: Google
4. Copy Web API Key

#### Step 4.3: Generate Service Account

1. Go to Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save as `firebase_service_account.json` in backend/
4. Update `.env` with credentials

#### Step 4.4: Update Frontend Config

```javascript
// templates/firebase-config.js
const firebaseConfig = {
  apiKey: "YOUR_WEB_API_KEY",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
  measurementId: "YOUR_MEASUREMENT_ID"
};
```

---

### Phase 5: Start Services

#### Terminal 1: Start Ollama (LLM Server)

```bash
ollama serve
# Server runs on: http://localhost:11434
```

#### Terminal 2: Start Backend (FastAPI)

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000
# API runs on: http://localhost:8000
# Docs on: http://localhost:8000/docs
```

#### Terminal 3: Start Frontend (Static Server)

```bash
cd <project-root>
python -m http.server 3000
# Frontend runs on: http://localhost:3000
```

---

## ✅ Verification Checklist

After setup, verify everything works:

```bash
# 1. Check Python
python --version  # Should be 3.8+

# 2. Check PostgreSQL
psql -U fraud_user -d fraud_detection_db -c "SELECT 1"

# 3. Check Ollama
curl http://localhost:11434/api/tags

# 4. Check Backend API
curl http://localhost:8000/health

# 5. Check Frontend
# Open browser: http://localhost:3000
```

---

## 🧪 Test the System

### Test Transaction (Should be FRAUD)

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_amount": 75000,
    "kyc_verified": "No",
    "account_age_days": 5,
    "channel": "international",
    "timestamp": "2025-11-01T03:00:00",
    "customer_segment": "Retail",
    "transaction_type": "Purchase"
  }'
```

**Expected Response:**
```json
{
  "is_fraud": true,
  "fraud_probability": 0.85,
  "risk_score": 0.82,
  "rules_triggered": [
    "high_amount_rule",
    "unverified_kyc_international",
    "new_account_high_amount",
    "odd_hours_rule"
  ]
}
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "Connection refused" (PostgreSQL)

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Verify connection
psql -U fraud_user -d fraud_detection_db
```

### Issue: "Connection refused" (Ollama)

**Solution:**
```bash
# Ensure Ollama is running
ollama serve

# Check model is loaded
ollama list
```

### Issue: "CORS error"

**Solution:**
Update `.env` CORS_ORIGINS:
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000
```

### Issue: Firebase authentication fails

**Solution:**
1. Verify firebase-config.js has correct credentials
2. Check Firebase project has Email/Password + Google enabled
3. Ensure service account JSON is in backend/

---

## 📦 Production Deployment

### Deploy to Cloud

**Option 1: Heroku**
```bash
# Install Heroku CLI
heroku login

# Create app
heroku create your-fraud-detection-app

# Set environment variables
heroku config:set DATABASE_URL=your_db_url
heroku config:set FIREBASE_PROJECT_ID=your_firebase_id

# Deploy
git push heroku main
```

**Option 2: AWS EC2**
```bash
# SSH into instance
ssh -i key.pem ubuntu@your-instance-ip

# Follow steps 1-5 above
# Use systemd to run services as background

# Example systemd service:
sudo tee /etc/systemd/system/fraud-api.service << EOF
[Unit]
Description=Fraud Detection API
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/fraud-detection
ExecStart=/home/ubuntu/fraud-detection/venv/bin/uvicorn app.main:app --port 8000

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable fraud-api.service
sudo systemctl start fraud-api.service
```

---

## ✨ Next Steps

1. ✅ Complete installation
2. ✅ Test single transaction
3. ✅ Upload CSV for bulk analysis
4. ✅ Check fraud alerts
5. ✅ Chat with AI assistant
6. ✅ Review model metrics
7. 📖 Read API documentation
8. 🚀 Deploy to production