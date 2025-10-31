# firebase.py - Firebase authentication service
import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
import logging
from typing import Dict, Any, Optional
from app.config import FIREBASE_CREDENTIALS_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseAuthService:
    """Firebase Authentication service"""
    
    def __init__(self):
        self.app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Use absolute path resolution
                base_dir = os.path.dirname(os.path.abspath(__file__))
                service_account_path = os.path.normpath(os.path.join(base_dir, "..", FIREBASE_CREDENTIALS_PATH))
                
                if not os.path.exists(service_account_path):
                    # Try the config path directly
                    service_account_path = FIREBASE_CREDENTIALS_PATH
                
                if not os.path.exists(service_account_path):
                    raise FileNotFoundError(f"Firebase service account file not found at: {service_account_path}")
                
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred)
                logger.info(f"Firebase Admin SDK initialized successfully with service account: {service_account_path}")
            else:
                self.app = firebase_admin.get_app()
                logger.info("Firebase Admin SDK already initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise
    
    async def verify_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user info"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            
            user_info = {
                "uid": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "firebase_provider": decoded_token.get("firebase", {}).get("sign_in_provider"),
                "auth_time": decoded_token.get("auth_time"),
                "exp": decoded_token.get("exp"),
                "iat": decoded_token.get("iat")
            }
            
            logger.info(f"Token verified successfully for user: {user_info['uid']}")
            return user_info
            
        except auth.ExpiredIdTokenError:
            logger.warning("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except auth.RevokedIdTokenError:
            logger.warning("Token has been revoked")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid token provided: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}"
            )
    
    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user record from Firebase by UID"""
        try:
            user_record = auth.get_user(uid)
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "email_verified": user_record.email_verified,
                "display_name": user_record.display_name,
                "photo_url": user_record.photo_url,
                "disabled": user_record.disabled,
                "creation_time": user_record.user_metadata.creation_timestamp,
                "last_sign_in_time": user_record.user_metadata.last_sign_in_timestamp,
                "provider_data": [
                    {
                        "provider_id": provider.provider_id,
                        "uid": provider.uid,
                        "email": provider.email,
                        "display_name": provider.display_name
                    }
                    for provider in user_record.provider_data
                ]
            }
        except auth.UserNotFoundError:
            logger.warning(f"User not found: {uid}")
            return None
        except Exception as e:
            logger.error(f"Error getting user by UID: {e}")
            raise
    
    async def create_custom_token(self, uid: str, additional_claims: Dict[str, Any] = None) -> str:
        """Create custom token for user"""
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            logger.info(f"Custom token created for user: {uid}")
            return custom_token.decode('utf-8')
        except Exception as e:
            logger.error(f"Error creating custom token: {e}")
            raise
    
    async def set_custom_user_claims(self, uid: str, custom_claims: Dict[str, Any]) -> bool:
        """Set custom claims for user"""
        try:
            auth.set_custom_user_claims(uid, custom_claims)
            logger.info(f"Custom claims set for user: {uid}")
            return True
        except Exception as e:
            logger.error(f"Error setting custom claims: {e}")
            raise
    
    async def disable_user(self, uid: str) -> bool:
        """Disable user account"""
        try:
            auth.update_user(uid, disabled=True)
            logger.info(f"User disabled: {uid}")
            return True
        except Exception as e:
            logger.error(f"Error disabling user: {e}")
            raise
    
    async def enable_user(self, uid: str) -> bool:
        """Enable user account"""
        try:
            auth.update_user(uid, disabled=False)
            logger.info(f"User enabled: {uid}")
            return True
        except Exception as e:
            logger.error(f"Error enabling user: {e}")
            raise
    
    async def delete_user(self, uid: str) -> bool:
        """Delete user account"""
        try:
            auth.delete_user(uid)
            logger.info(f"User deleted: {uid}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise
    
    async def list_users(self, page_token: str = None, max_results: int = 1000) -> Dict[str, Any]:
        """List all users (admin function)"""
        try:
            page = auth.list_users(page_token=page_token, max_results=max_results)
            users = []
            for user in page.users:
                users.append({
                    "uid": user.uid,
                    "email": user.email,
                    "display_name": user.display_name,
                    "disabled": user.disabled,
                    "email_verified": user.email_verified,
                    "creation_time": user.user_metadata.creation_timestamp,
                    "last_sign_in_time": user.user_metadata.last_sign_in_timestamp
                })
            
            return {
                "users": users,
                "next_page_token": page.next_page_token,
                "has_next_page": page.has_next_page
            }
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            raise
    
    async def update_user(self, uid: str, **kwargs) -> bool:
        """Update user properties"""
        try:
            auth.update_user(uid, **kwargs)
            logger.info(f"User updated: {uid}")
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise
    
    async def send_password_reset_email(self, email: str) -> bool:
        """Send password reset email"""
        try:
            # This requires Firebase Auth REST API
            # Implementation would depend on your specific needs
            logger.info(f"Password reset email would be sent to: {email}")
            return True
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get Firebase service health status"""
        try:
            if self.app:
                return {
                    "status": "healthy",
                    "firebase_initialized": True,
                    "app_name": self.app.name,
                    "project_id": self.app.project_id
                }
            else:
                return {
                    "status": "unhealthy",
                    "firebase_initialized": False,
                    "error": "Firebase app not initialized"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "firebase_initialized": False,
                "error": str(e)
            }

# Global Firebase service instance
firebase_service = FirebaseAuthService()

async def verify_token(token: str) -> Dict[str, Any]:
    """Verify Firebase token (convenience function)"""
    return await firebase_service.verify_token(token)

async def get_user_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    """Get user by UID (convenience function)"""
    return await firebase_service.get_user_by_uid(uid)

def get_firebase_service() -> FirebaseAuthService:
    """Get Firebase service instance"""
    return firebase_service

def get_firebase_health() -> Dict[str, Any]:
    """Get Firebase health status"""
    return firebase_service.get_health_status()
