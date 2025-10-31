# services.py - Business logic, ML model, LLM, and rule engine
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import joblib
import datetime
import uuid
import json
import logging
import httpx
import asyncio
from typing import Dict, List, Tuple, Optional, Any
from app.config import (
    MODEL_PATH, SCALER_PATH, ENCODER_PATH, OLLAMA_URL, LLAMA_MODEL,
    FRAUD_THRESHOLD, FEATURE_DIM, SEQUENCE_LENGTH, LLM_TIMEOUT, 
    LLM_MAX_TOKENS, LLM_TEMPERATURE, OPENAI_API_KEY
)
from app.schemas import TransactionPredict, PredictionResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegularizedHybridModel(nn.Module):
    """Hybrid LSTM + Transformer model for fraud detection"""
    
    def __init__(self, feature_dim, lstm_hidden_dim=64, lstm_layers=1,
                 transformer_layers=2, nhead=4, transformer_dim=128, output_dim=1, dropout=0.3):
        super(RegularizedHybridModel, self).__init__()
        
        self.lstm = nn.LSTM(input_size=feature_dim,
                            hidden_size=lstm_hidden_dim,
                            num_layers=lstm_layers,
                            batch_first=True,
                            dropout=dropout if lstm_layers > 1 else 0)
        
        self.positional_encoding = nn.Parameter(torch.zeros(1, 500, lstm_hidden_dim))
        
        encoder_layer = nn.TransformerEncoderLayer(d_model=lstm_hidden_dim,
                                                   nhead=nhead,
                                                   dim_feedforward=transformer_dim,
                                                   dropout=dropout,
                                                   batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=transformer_layers)
        
        self.output_layer = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(lstm_hidden_dim, output_dim)
        )
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        seq_len = lstm_out.size(1)
        pos_enc = self.positional_encoding[:, :seq_len, :]
        x_transformed = lstm_out + pos_enc
        transformer_out = self.transformer_encoder(x_transformed)
        pooled = transformer_out.mean(dim=1)
        out = self.output_layer(pooled)
        return out

class MLModelService:
    """Service for loading and running ML model predictions"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.encoder = None
        self.feature_dim = FEATURE_DIM
        self.fraud_threshold = FRAUD_THRESHOLD
        self.sequence_length = SEQUENCE_LENGTH
        self.model_version = "v1.0"
        self.load_model()
    
    def load_model(self):
        """Load model, scaler, and encoder"""
        try:
            # Load PyTorch model
            self.model = RegularizedHybridModel(feature_dim=self.feature_dim)
            state_dict = torch.load(MODEL_PATH, map_location=torch.device('cpu'))
            self.model.load_state_dict(state_dict)
            self.model.eval()
            logger.info("PyTorch model loaded successfully")
            
            # Load preprocessing components
            self.scaler = joblib.load(SCALER_PATH)
            self.encoder = joblib.load(ENCODER_PATH)
            logger.info("Scaler and encoder loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model components: {e}")
            raise
    
    def preprocess_transaction(self, transaction_data: dict) -> np.ndarray:
        """Preprocess transaction data for model input"""
        try:
            # Extract basic features
            account_age_days = transaction_data['account_age_days']
            transaction_amount = transaction_data['transaction_amount']
            timestamp = pd.to_datetime(transaction_data['timestamp'])
            
            # Extract time features
            hour = timestamp.hour
            weekday = timestamp.weekday()
            month = timestamp.month
            
            # Calculate derived features
            is_high_value = 1 if transaction_amount > 50000 else 0
            time_since_last_txn = 0
            rolling_avg_txn_amount = transaction_amount
            txn_deviation_from_avg = 0
            customer_transaction_count = 1
            unique_channels_used = 1
            
            # Create numeric features array (11 features)
            numeric_features = np.array([[
                account_age_days, transaction_amount, hour, weekday, month,
                is_high_value, time_since_last_txn, rolling_avg_txn_amount,
                txn_deviation_from_avg, customer_transaction_count, unique_channels_used
            ]])
            
            # Scale numeric features
            scaled_numeric = self.scaler.transform(numeric_features)
            
            # Prepare categorical features
            kyc_verified = transaction_data['kyc_verified']
            channel = transaction_data['channel']
            customer_segment = transaction_data.get('customer_segment', 'Retail')
            transaction_type = transaction_data.get('transaction_type', 'Purchase')
            
            # Encode categorical features
            try:
                categorical_features = [[kyc_verified, channel, customer_segment, transaction_type]]
                encoded_result = self.encoder.transform(categorical_features)
            except ValueError:
                # Fallback to 2 features if encoder was trained with fewer
                categorical_features = [[kyc_verified, channel]]
                encoded_result = self.encoder.transform(categorical_features)
            
            # Handle both sparse and dense arrays
            if hasattr(encoded_result, 'toarray'):
                encoded_categorical = encoded_result.toarray()
            else:
                encoded_categorical = encoded_result
            
            # Combine features
            combined_features = np.concatenate([scaled_numeric, encoded_categorical], axis=1)
            
            # Create sequence for LSTM model
            sequence = np.repeat(combined_features, self.sequence_length, axis=0).reshape(1, self.sequence_length, -1)
            
            return sequence
            
        except Exception as e:
            logger.error(f"Error preprocessing transaction: {e}")
            raise
    
    def predict(self, preprocessed_data: np.ndarray) -> Tuple[float, bool]:
        """Make fraud prediction using the ML model"""
        try:
            with torch.no_grad():
                input_tensor = torch.tensor(preprocessed_data, dtype=torch.float32)
                logits = self.model(input_tensor)
                probability = torch.sigmoid(logits).item()
                is_fraud = probability > self.fraud_threshold
                
                return probability, is_fraud
                
        except Exception as e:
            logger.error(f"Error making ML prediction: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "version": self.model_version,
            "feature_dim": self.feature_dim,
            "sequence_length": self.sequence_length,
            "fraud_threshold": self.fraud_threshold,
            "model_loaded": self.model is not None
        }

class RuleEngineService:
    """Service for business rule-based fraud detection"""
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict[str, dict]:
        """Initialize fraud detection rules"""
        return {
            "high_amount_rule": {
                "description": "Flag transactions above 5x user average amount",
                "priority": 1,
                "active": True,
                "threshold_multiplier": 5.0
            },
            "unverified_kyc_international": {
                "description": "Flag international transactions with unverified KYC",
                "priority": 2,
                "active": True
            },
            "odd_hours_rule": {
                "description": "Flag transactions during odd hours (2AM-4AM)",
                "priority": 3,
                "active": True,
                "start_hour": 2,
                "end_hour": 4
            },
            "new_account_high_amount": {
                "description": "Flag high amounts from accounts < 30 days old",
                "priority": 4,
                "active": True,
                "account_age_threshold": 30,
                "amount_threshold": 5000
            },
            "weekend_high_amount": {
                "description": "Flag high amount transactions on weekends",
                "priority": 5,
                "active": True,
                "amount_threshold": 10000
            }
        }
    
    def apply_rules(self, transaction_data: dict, user_avg_amount: float = 1000.0) -> Tuple[List[str], str, float]:
        """Apply business rules and return triggered rules, reason, and rule score"""
        triggered_rules = []
        reasons = []
        rule_scores = []
        
        amount = transaction_data['transaction_amount']
        channel = transaction_data['channel']
        kyc_verified = transaction_data['kyc_verified']
        account_age = transaction_data['account_age_days']
        timestamp = pd.to_datetime(transaction_data['timestamp'])
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # Rule 1: High amount rule
        if (self.rules["high_amount_rule"]["active"] and 
            amount > self.rules["high_amount_rule"]["threshold_multiplier"] * user_avg_amount):
            triggered_rules.append("high_amount_rule")
            reasons.append(f"Amount ${amount:,.2f} is {amount/user_avg_amount:.1f}x higher than average")
            rule_scores.append(0.8)
        
        # Rule 2: Unverified KYC international
        if (self.rules["unverified_kyc_international"]["active"] and 
            channel == "international" and kyc_verified == "No"):
            triggered_rules.append("unverified_kyc_international")
            reasons.append("International transaction with unverified KYC")
            rule_scores.append(0.9)
        
        # Rule 3: Odd hours
        start_hour = self.rules["odd_hours_rule"]["start_hour"]
        end_hour = self.rules["odd_hours_rule"]["end_hour"]
        if (self.rules["odd_hours_rule"]["active"] and 
            start_hour <= hour <= end_hour):
            triggered_rules.append("odd_hours_rule")
            reasons.append(f"Transaction at unusual hour ({hour:02d}:00)")
            rule_scores.append(0.6)
        
        # Rule 4: New account high amount
        if (self.rules["new_account_high_amount"]["active"] and 
            account_age < self.rules["new_account_high_amount"]["account_age_threshold"] and
            amount > self.rules["new_account_high_amount"]["amount_threshold"]):
            triggered_rules.append("new_account_high_amount")
            reasons.append(f"High amount ${amount:,.2f} from new account ({account_age} days)")
            rule_scores.append(0.7)
        
        # Rule 5: Weekend high amount
        if (self.rules["weekend_high_amount"]["active"] and 
            weekday >= 5 and amount > self.rules["weekend_high_amount"]["amount_threshold"]):
            triggered_rules.append("weekend_high_amount")
            reasons.append(f"High weekend transaction (${amount:,.2f})")
            rule_scores.append(0.5)
        
        # Calculate combined rule score
        combined_rule_score = max(rule_scores) if rule_scores else 0.0
        combined_reason = "; ".join(reasons) if reasons else "No rules triggered"
        
        return triggered_rules, combined_reason, combined_rule_score

class LlamaLLMService:
    """Service for local Llama 3 via Ollama API"""
    
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model_name = LLAMA_MODEL
        self.timeout = LLM_TIMEOUT
        self.max_tokens = LLM_MAX_TOKENS
        self.temperature = LLM_TEMPERATURE
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Ollama API"""
        try:
            import requests
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"Ollama API connection successful")
            else:
                logger.warning(f"Ollama API responded with status {response.status_code}")
        except Exception as e:
            logger.warning(f"Cannot connect to Ollama API: {e}")
    
    async def generate_explanation(self, transaction_data: dict, prediction_result: dict, 
                                 rules_triggered: List[str]) -> str:
        """Generate fraud explanation using local Llama 3"""
        try:
            prompt = self._create_explanation_prompt(transaction_data, prediction_result, rules_triggered)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "top_p": 0.9,
                            "num_predict": self.max_tokens
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    explanation = result.get("response", "").strip()
                    
                    if explanation and len(explanation) > 20:
                        return self._clean_explanation(explanation)
                    else:
                        return self._generate_fallback_explanation(transaction_data, prediction_result, rules_triggered)
                else:
                    return self._generate_fallback_explanation(transaction_data, prediction_result, rules_triggered)
                    
        except Exception as e:
            logger.error(f"Error calling Llama 3: {e}")
            return self._generate_fallback_explanation(transaction_data, prediction_result, rules_triggered)
    
    def _create_explanation_prompt(self, transaction_data: dict, prediction_result: dict, rules_triggered: List[str]) -> str:
        """Create prompt for fraud explanation"""
        fraud_status = "FRAUDULENT" if prediction_result.get('is_fraud', False) else "LEGITIMATE"
        
        prompt = f"""You are a fraud detection expert. Analyze this transaction and provide a clear explanation.

TRANSACTION DETAILS:
- Amount: ${transaction_data['transaction_amount']:,.2f}
- Channel: {transaction_data['channel']}
- KYC Status: {transaction_data['kyc_verified']}
- Account Age: {transaction_data['account_age_days']} days
- Time: {transaction_data['timestamp']}

ANALYSIS RESULTS:
- Classification: {fraud_status}
- AI Fraud Probability: {prediction_result.get('fraud_probability', 0):.1%}
- Risk Score: {prediction_result.get('risk_score', 0):.1%}
- Business Rules Triggered: {', '.join(rules_triggered) if rules_triggered else 'None'}

Explain in 2-3 clear sentences why this transaction was classified as {fraud_status.lower()}. Focus on key risk factors.

Explanation:"""
        return prompt
    
    def _clean_explanation(self, explanation: str) -> str:
        """Clean and format the explanation"""
        lines = explanation.split('\n')
        cleaned = ' '.join([line.strip() for line in lines if line.strip() and not line.startswith('Explanation:')])
        
        if len(cleaned) > 500:
            sentences = cleaned.split('. ')
            cleaned = '. '.join(sentences[:3]) + '.'
        
        return cleaned
    
    async def chat(self, message: str, user_id: int, context: Optional[Dict] = None) -> str:
        """Handle chat with LLM"""
        try:
            chat_prompt = self._create_chat_prompt(message, context)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": chat_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": 400
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "").strip()
                    return response_text if response_text else "I couldn't generate a response. Please try again."
                else:
                    return "I'm having trouble right now. Please try again later."
                    
        except Exception as e:
            logger.error(f"Error in LLM chat: {e}")
            return "I apologize, but I'm experiencing technical difficulties."
    
    def _create_chat_prompt(self, message: str, context: Optional[Dict] = None) -> str:
        """Create chat prompt"""
        system_context = """You are a helpful fraud detection assistant. You help users understand fraud detection, financial security, and transaction risk factors. Keep responses helpful and concise."""
        
        context_info = ""
        if context:
            context_info = f"\nUser context: {context.get('recent_fraud_count', 0)} recent fraud alerts.\n"
        
        return f"{system_context}{context_info}\n\nUser: {message}\n\nAssistant:"
    
    def _generate_fallback_explanation(self, transaction_data: dict, prediction_result: dict, rules_triggered: List[str]) -> str:
        """Generate fallback explanation"""
        if prediction_result.get('is_fraud', False):
            risk_factors = []
            
            if "high_amount_rule" in rules_triggered:
                risk_factors.append(f"unusually high amount (${transaction_data['transaction_amount']:,.2f})")
            if "unverified_kyc_international" in rules_triggered:
                risk_factors.append("international transaction with unverified KYC")
            if "odd_hours_rule" in rules_triggered:
                risk_factors.append("transaction during unusual hours")
            if "new_account_high_amount" in rules_triggered:
                risk_factors.append(f"high amount from new account")
            
            if risk_factors:
                return f"This transaction is flagged as fraudulent due to: {', '.join(risk_factors)}. The AI model assigned a {prediction_result.get('fraud_probability', 0):.1%} fraud probability."
        
        return f"This transaction appears legitimate with a {prediction_result.get('fraud_probability', 0):.1%} fraud probability."
    
    async def health_check(self) -> Dict[str, Any]:
        """Check LLM service health"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "ollama_available": True,
                        "model_name": self.model_name,
                        "url": self.ollama_url
                    }
                else:
                    return {"status": "unhealthy", "ollama_available": False}
        except Exception as e:
            return {"status": "unhealthy", "ollama_available": False, "error": str(e)}

class FraudDetectionService:
    """Main service combining ML model, rule engine, and LLM"""
    
    def __init__(self):
        self.ml_service = MLModelService()
        self.rule_service = RuleEngineService()
        self.llm_service = LlamaLLMService()
        self.model_version = "v1.0"
    
    def predict_fraud(self, transaction_data: dict, user_avg_amount: float = 1000.0) -> PredictionResult:
        """Complete fraud prediction combining ML, rules"""
        try:
            transaction_id = transaction_data.get('transaction_id', str(uuid.uuid4()))
            
            # ML prediction
            preprocessed_data = self.ml_service.preprocess_transaction(transaction_data)
            ml_probability, ml_is_fraud = self.ml_service.predict(preprocessed_data)
            
            # Business rules
            triggered_rules, rule_reason, rule_score = self.rule_service.apply_rules(transaction_data, user_avg_amount)
            
            # Combine results
            rule_triggered = len(triggered_rules) > 0
            final_is_fraud = ml_is_fraud or rule_triggered
            
            # Calculate risk score
            ml_weight = 0.7
            rule_weight = 0.3
            risk_score = ml_weight * ml_probability + rule_weight * rule_score
            risk_score = min(risk_score, 1.0)
            
            # Create reason
            if final_is_fraud:
                if ml_is_fraud and rule_triggered:
                    reason = f"Both AI model (confidence: {ml_probability:.1%}) and business rules flagged this transaction. Rules: {rule_reason}"
                elif ml_is_fraud:
                    reason = f"AI model flagged with {ml_probability:.1%} fraud probability"
                else:
                    reason = f"Business rules flagged: {rule_reason}"
            else:
                reason = f"Transaction appears legitimate (AI confidence: {ml_probability:.1%})"
            
            return PredictionResult(
                transaction_id=transaction_id,
                is_fraud=final_is_fraud,
                fraud_probability=ml_probability,
                risk_score=risk_score,
                prediction_confidence=ml_probability,
                model_version=self.model_version,
                rules_triggered=triggered_rules,
                reason=reason,
                timestamp=datetime.datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error in fraud prediction: {e}")
            raise
    
    async def predict_fraud_with_explanation(self, transaction_data: dict, user_avg_amount: float = 1000.0) -> PredictionResult:
        """Fraud prediction with LLM explanation"""
        result = self.predict_fraud(transaction_data, user_avg_amount)
        
        try:
            llm_explanation = await self.llm_service.generate_explanation(
                transaction_data, result.dict(), result.rules_triggered
            )
            result.llm_explanation = llm_explanation
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            result.llm_explanation = "Explanation generation unavailable."
        
        return result
    
    async def chat_with_llm(self, message: str, user_id: int, context: Optional[Dict] = None) -> str:
        """Chat with LLM"""
        return await self.llm_service.chat(message, user_id, context)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health"""
        ml_info = self.ml_service.get_model_info()
        return {
            "ml_service": ml_info,
            "rule_engine": {
                "active_rules": sum(1 for rule in self.rule_service.rules.values() if rule["active"]),
                "total_rules": len(self.rule_service.rules)
            },
            "model_version": self.model_version
        }

# Global service instances
fraud_detection_service = FraudDetectionService()

def get_fraud_detection_service() -> FraudDetectionService:
    return fraud_detection_service

def get_llm_service() -> LlamaLLMService:
    return fraud_detection_service.llm_service
