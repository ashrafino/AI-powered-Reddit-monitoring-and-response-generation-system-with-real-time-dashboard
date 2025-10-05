from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass
import bcrypt
import logging

from fastapi import HTTPException, status
from jose import jwt, JWTError
from passlib.context import CryptContext

from .config import settings

# Set up logger for authentication
auth_logger = logging.getLogger("auth")

# Initialize bcrypt context with optimal settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    default="bcrypt",
    bcrypt__default_rounds=12,
    bcrypt__salt_size=22,  # Bcrypt requires exactly 22 characters for salt
    deprecated="auto"
)
ALGORITHM = "HS256"


@dataclass
class TokenPayload:
    """JWT token payload structure"""
    sub: str  # user email
    client_id: Optional[int]
    user_id: int
    exp: datetime
    iat: datetime


class TokenValidationResult:
    """Result of token validation with detailed information"""
    def __init__(self, is_valid: bool, payload: Optional[TokenPayload] = None, 
                 error: Optional[str] = None, error_code: Optional[str] = None):
        self.is_valid = is_valid
        self.payload = payload
        self.error = error
        self.error_code = error_code


class AuthErrorCodes:
    """Standard error codes for authentication failures"""
    TOKEN_MISSING = "TOKEN_MISSING"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_MISSING_SUBJECT = "TOKEN_MISSING_SUBJECT"
    TOKEN_MISSING_USER_ID = "TOKEN_MISSING_USER_ID"
    TOKEN_MISSING_EXPIRATION = "TOKEN_MISSING_EXPIRATION"
    TOKEN_INVALID_TIMESTAMP = "TOKEN_INVALID_TIMESTAMP"
    TOKEN_INVALID_FORMAT = "TOKEN_INVALID_FORMAT"
    TOKEN_VALIDATION_ERROR = "TOKEN_VALIDATION_ERROR"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_INACTIVE = "USER_INACTIVE"
    CLIENT_NOT_FOUND = "CLIENT_NOT_FOUND"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"


class AuthenticationError(HTTPException):
    """Custom authentication error with detailed error codes"""
    def __init__(self, detail: str, error_code: str = None, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )
        self.error_code = error_code


class AuthLogger:
    """Authentication logger for tracking auth events"""
    
    @staticmethod
    def log_auth_success(user_email: str, client_id: Optional[int], endpoint: str, user_id: int, 
                        ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                        request_id: Optional[str] = None, session_id: Optional[str] = None):
        """Log successful authentication"""
        auth_logger.info(
            f"AUTH_SUCCESS: user={user_email}, user_id={user_id}, client_id={client_id}, endpoint={endpoint}"
        )
        
        # Store in database for audit trail
        try:
            from app.models.auth_audit import AuthAuditLog
            from app.db.session import SessionLocal
            
            db = SessionLocal()
            try:
                audit_log = AuthAuditLog(
                    user_email=user_email,
                    user_id=user_id,
                    client_id=client_id,
                    event_type="authentication_success",
                    success=True,
                    endpoint=endpoint,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    session_id=session_id
                )
                db.add(audit_log)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            auth_logger.error(f"Failed to write auth success audit log: {str(e)}")
    
    @staticmethod
    def log_auth_failure(
        error_code: str, 
        detail: str, 
        endpoint: str,
        token_info: Optional[Dict] = None,
        user_email: Optional[str] = None,
        user_id: Optional[int] = None,
        client_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Log authentication failure with context"""
        log_msg = f"AUTH_FAILURE: error_code={error_code}, detail={detail}, endpoint={endpoint}"
        if user_email:
            log_msg += f", user={user_email}"
        if token_info:
            log_msg += f", token_debug={token_info}"
        
        auth_logger.warning(log_msg)
        
        # Store in database for audit trail
        try:
            from app.models.auth_audit import AuthAuditLog
            from app.db.session import SessionLocal
            
            db = SessionLocal()
            try:
                audit_log = AuthAuditLog(
                    user_email=user_email,
                    user_id=user_id,
                    client_id=client_id,
                    event_type="authentication_failure",
                    success=False,
                    error_code=error_code,
                    error_detail=detail,
                    endpoint=endpoint,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    session_id=session_id,
                    additional_data=token_info
                )
                db.add(audit_log)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            auth_logger.error(f"Failed to write auth failure audit log: {str(e)}")
    
    @staticmethod
    def log_token_creation(user_email: str, user_id: int, client_id: Optional[int],
                          ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                          request_id: Optional[str] = None, session_id: Optional[str] = None):
        """Log token creation"""
        auth_logger.info(
            f"TOKEN_CREATED: user={user_email}, user_id={user_id}, client_id={client_id}"
        )
        
        # Store in database for audit trail
        try:
            from app.models.auth_audit import AuthAuditLog
            from app.db.session import SessionLocal
            
            db = SessionLocal()
            try:
                audit_log = AuthAuditLog(
                    user_email=user_email,
                    user_id=user_id,
                    client_id=client_id,
                    event_type="token_creation",
                    success=True,
                    endpoint="login",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    session_id=session_id
                )
                db.add(audit_log)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            auth_logger.error(f"Failed to write token creation audit log: {str(e)}")
    
    @staticmethod
    def log_token_validation_failure(error_code: str, error_detail: str, token_partial: str = None,
                                   ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                                   request_id: Optional[str] = None, session_id: Optional[str] = None):
        """Log token validation failure"""
        log_msg = f"TOKEN_VALIDATION_FAILED: error_code={error_code}, detail={error_detail}"
        if token_partial:
            log_msg += f", token_start={token_partial[:20]}..."
        
        auth_logger.warning(log_msg)
        
        # Store in database for audit trail
        try:
            from app.models.auth_audit import AuthAuditLog
            from app.db.session import SessionLocal
            
            db = SessionLocal()
            try:
                audit_log = AuthAuditLog(
                    event_type="token_validation_failure",
                    success=False,
                    error_code=error_code,
                    error_detail=error_detail,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    session_id=session_id,
                    additional_data={"token_partial": token_partial} if token_partial else None
                )
                db.add(audit_log)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            auth_logger.error(f"Failed to write token validation failure audit log: {str(e)}")


def create_access_token(
    user_email: str, 
    user_id: int,
    client_id: Optional[int] = None,
    expires_minutes: Optional[int] = None
) -> str:
    """Create JWT token with proper payload structure including client_id and user_id"""
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expire_minutes)
    
    to_encode = {
        "sub": user_email,
        "user_id": user_id,
        "client_id": client_id,
        "exp": expire,
        "iat": now
    }
    
    token = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    
    # Log token creation
    AuthLogger.log_token_creation(user_email, user_id, client_id)
    
    return token


def verify_token(token: str) -> TokenValidationResult:
    """Verify and decode JWT token with comprehensive error handling"""
    token_partial = token[:20] if token else "None"
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        
        # Extract required fields
        subject = payload.get("sub")
        user_id = payload.get("user_id")
        client_id = payload.get("client_id")
        exp = payload.get("exp")
        iat = payload.get("iat")
        
        # Validate required fields
        if not subject:
            error_code = AuthErrorCodes.TOKEN_MISSING_SUBJECT
            error_msg = "Token missing subject (user email)"
            AuthLogger.log_token_validation_failure(error_code, error_msg, token_partial)
            return TokenValidationResult(
                is_valid=False,
                error=error_msg,
                error_code=error_code
            )
        
        if not user_id:
            error_code = AuthErrorCodes.TOKEN_MISSING_USER_ID
            error_msg = "Token missing user_id"
            AuthLogger.log_token_validation_failure(error_code, error_msg, token_partial)
            return TokenValidationResult(
                is_valid=False,
                error=error_msg,
                error_code=error_code
            )
        
        if not exp:
            error_code = AuthErrorCodes.TOKEN_MISSING_EXPIRATION
            error_msg = "Token missing expiration"
            AuthLogger.log_token_validation_failure(error_code, error_msg, token_partial)
            return TokenValidationResult(
                is_valid=False,
                error=error_msg,
                error_code=error_code
            )
        
        # Convert timestamps
        try:
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            iat_datetime = datetime.fromtimestamp(iat, tz=timezone.utc) if iat else None
        except (ValueError, TypeError) as e:
            error_code = AuthErrorCodes.TOKEN_INVALID_TIMESTAMP
            error_msg = f"Invalid timestamp in token: {str(e)}"
            AuthLogger.log_token_validation_failure(error_code, error_msg, token_partial)
            return TokenValidationResult(
                is_valid=False,
                error=error_msg,
                error_code=error_code
            )
        
        # Check if token is expired
        if exp_datetime < datetime.now(timezone.utc):
            error_code = AuthErrorCodes.TOKEN_EXPIRED
            error_msg = "Token has expired"
            AuthLogger.log_token_validation_failure(error_code, error_msg, token_partial)
            return TokenValidationResult(
                is_valid=False,
                error=error_msg,
                error_code=error_code
            )
        
        token_payload = TokenPayload(
            sub=subject,
            user_id=user_id,
            client_id=client_id,
            exp=exp_datetime,
            iat=iat_datetime or datetime.now(timezone.utc)
        )
        
        return TokenValidationResult(is_valid=True, payload=token_payload)
        
    except JWTError as e:
        error_code = AuthErrorCodes.TOKEN_INVALID_FORMAT
        error_msg = f"JWT decode error: {str(e)}"
        AuthLogger.log_token_validation_failure(error_code, error_msg, token_partial)
        return TokenValidationResult(
            is_valid=False,
            error=error_msg,
            error_code=error_code
        )
    except Exception as e:
        error_code = AuthErrorCodes.TOKEN_VALIDATION_ERROR
        error_msg = f"Unexpected error during token validation: {str(e)}"
        AuthLogger.log_token_validation_failure(error_code, error_msg, token_partial)
        return TokenValidationResult(
            is_valid=False,
            error=error_msg,
            error_code=error_code
        )


def get_token_info(token: str) -> Dict[str, Any]:
    """Get token information for debugging purposes"""
    try:
        # Decode without verification to get payload info
        unverified_payload = jwt.get_unverified_claims(token)
        
        # Get header info
        unverified_header = jwt.get_unverified_header(token)
        
        # Verify the token to get validation status
        validation_result = verify_token(token)
        
        return {
            "header": unverified_header,
            "payload": unverified_payload,
            "is_valid": validation_result.is_valid,
            "validation_error": validation_result.error,
            "error_code": validation_result.error_code,
            "decoded_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "error": f"Could not decode token: {str(e)}",
            "decoded_at": datetime.now(timezone.utc).isoformat()
        }


# Legacy function for backward compatibility
def create_access_token_legacy(subject: str, expires_minutes: Optional[int] = None) -> str:
    """Legacy function for backward compatibility - use create_access_token instead"""
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)



