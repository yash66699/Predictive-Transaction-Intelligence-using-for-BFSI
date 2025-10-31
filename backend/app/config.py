import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Database config
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://fraud_user:your_strong_password@localhost:5432/fraud_detection_db"
)

# Firebase credentials path
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase_service_account.json")

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")

# Model paths
MODEL_PATH = os.getenv("MODEL_PATH", "./models/4th_model.pth")
SCALER_PATH = os.getenv("SCALER_PATH", "./models/scaler.joblib")
ENCODER_PATH = os.getenv("ENCODER_PATH", "./models/encoder.joblib")

# Ollama/LLM Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama3")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "300"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# OpenAI Configuration (Optional fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# API Settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "True").lower() == "true"

# CORS Allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://localhost:8081",  # For dev
    "*"  # Remove in production
]

# Security settings
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"

# Fraud detection settings
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.3"))
FEATURE_DIM = int(os.getenv("FEATURE_DIM", "15"))
SEQUENCE_LENGTH = int(os.getenv("SEQUENCE_LENGTH", "10"))

# File upload settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
ALLOWED_FILE_TYPES = ["csv", "xlsx", "xls"]

# Rate limiting
RATE_LIMIT_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "100"))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
