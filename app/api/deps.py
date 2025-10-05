from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    verify_token, 
    AuthenticationError, 
    AuthErrorCodes, 
    AuthLogger
)
from app.db.session import get_db
from app.models.user import User
from app.middleware.security import extract_client_info

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")
ALGORITHM = "HS256"


def get_current_user(
    request: Request,
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """Enhanced user authentication with better error handling"""
    
    # Extract client info for audit logging
    client_info = extract_client_info(request)
    
    # Verify token using enhanced validation
    validation_result = verify_token(token)
    
    if not validation_result.is_valid:
        AuthLogger.log_auth_failure(
            error_code=validation_result.error_code,
            detail=validation_result.error,
            endpoint="get_current_user",
            **client_info
        )
        raise AuthenticationError(
            detail=validation_result.error,
            error_code=validation_result.error_code
        )
    
    # Get user from database
    user = db.query(User).filter(User.email == validation_result.payload.sub).first()
    if user is None:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.USER_NOT_FOUND,
            detail="User not found",
            endpoint="get_current_user",
            user_email=validation_result.payload.sub,
            **client_info
        )
        raise AuthenticationError(
            detail="User not found",
            error_code=AuthErrorCodes.USER_NOT_FOUND
        )
    
    if not user.is_active:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.USER_INACTIVE,
            detail="User account is inactive",
            endpoint="get_current_user",
            user_email=user.email,
            user_id=user.id,
            **client_info
        )
        raise AuthenticationError(
            detail="User account is inactive",
            error_code=AuthErrorCodes.USER_INACTIVE
        )
    
    # Verify user_id matches token
    if user.id != validation_result.payload.user_id:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.TOKEN_INVALID,
            detail="Token user_id does not match database user",
            endpoint="get_current_user",
            user_email=user.email,
            user_id=user.id,
            **client_info
        )
        raise AuthenticationError(
            detail="Invalid token user information",
            error_code=AuthErrorCodes.TOKEN_INVALID
        )
    
    # Log successful authentication
    AuthLogger.log_auth_success(
        user_email=user.email,
        client_id=validation_result.payload.client_id,
        endpoint="get_current_user",
        user_id=user.id,
        **client_info
    )
    
    return user


def get_current_user_with_client(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Tuple[User, Optional[int]]:
    """Get user and client_id together for client-scoped operations"""
    
    # Extract client info for audit logging
    client_info = extract_client_info(request)
    
    # Verify token using enhanced validation
    validation_result = verify_token(token)
    
    if not validation_result.is_valid:
        AuthLogger.log_auth_failure(
            error_code=validation_result.error_code,
            detail=validation_result.error,
            endpoint="get_current_user_with_client",
            **client_info
        )
        raise AuthenticationError(
            detail=validation_result.error,
            error_code=validation_result.error_code
        )
    
    # Get user from database
    user = db.query(User).filter(User.email == validation_result.payload.sub).first()
    if user is None:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.USER_NOT_FOUND,
            detail="User not found",
            endpoint="get_current_user_with_client",
            user_email=validation_result.payload.sub,
            **client_info
        )
        raise AuthenticationError(
            detail="User not found",
            error_code=AuthErrorCodes.USER_NOT_FOUND
        )
    
    if not user.is_active:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.USER_INACTIVE,
            detail="User account is inactive",
            endpoint="get_current_user_with_client",
            user_email=user.email,
            user_id=user.id,
            **client_info
        )
        raise AuthenticationError(
            detail="User account is inactive",
            error_code=AuthErrorCodes.USER_INACTIVE
        )
    
    # Verify user_id matches token
    if user.id != validation_result.payload.user_id:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.TOKEN_INVALID,
            detail="Token user_id does not match database user",
            endpoint="get_current_user_with_client",
            user_email=user.email,
            user_id=user.id,
            **client_info
        )
        raise AuthenticationError(
            detail="Invalid token user information",
            error_code=AuthErrorCodes.TOKEN_INVALID
        )
    
    # Verify client_id matches if user has a client
    token_client_id = validation_result.payload.client_id
    if user.client_id and token_client_id != user.client_id:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.CLIENT_NOT_FOUND,
            detail="Token client_id does not match user's client",
            endpoint="get_current_user_with_client",
            user_email=user.email,
            user_id=user.id,
            client_id=user.client_id,
            **client_info
        )
        raise AuthenticationError(
            detail="Invalid client information in token",
            error_code=AuthErrorCodes.CLIENT_NOT_FOUND
        )
    
    # Log successful authentication
    AuthLogger.log_auth_success(
        user_email=user.email,
        client_id=token_client_id,
        endpoint="get_current_user_with_client",
        user_id=user.id,
        **client_info
    )
    
    return user, token_client_id


def require_admin(
    request: Request,
    user: User = Depends(get_current_user)
) -> User:
    """Require admin role with enhanced error handling"""
    if user.role != "admin":
        client_info = extract_client_info(request)
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.INSUFFICIENT_PERMISSIONS,
            detail="Admin access required",
            endpoint="require_admin",
            user_email=user.email,
            user_id=user.id,
            **client_info
        )
        raise AuthenticationError(
            detail="Admin access required",
            error_code=AuthErrorCodes.INSUFFICIENT_PERMISSIONS,
            status_code=status.HTTP_403_FORBIDDEN
        )
    return user


async def websocket_auth_dependency(
    token: str = Query(...),
    db: Session = Depends(get_db)
) -> Tuple[User, Optional[int]]:
    """WebSocket-specific authentication dependency"""
    
    # Verify token using enhanced validation
    validation_result = verify_token(token)
    
    if not validation_result.is_valid:
        AuthLogger.log_auth_failure(
            error_code=validation_result.error_code,
            detail=validation_result.error,
            endpoint="websocket_auth"
        )
        raise AuthenticationError(
            detail=validation_result.error,
            error_code=validation_result.error_code
        )
    
    # Get user from database
    user = db.query(User).filter(User.email == validation_result.payload.sub).first()
    if user is None:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.USER_NOT_FOUND,
            detail="User not found",
            endpoint="websocket_auth",
            user_email=validation_result.payload.sub
        )
        raise AuthenticationError(
            detail="User not found",
            error_code=AuthErrorCodes.USER_NOT_FOUND
        )
    
    if not user.is_active:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.USER_INACTIVE,
            detail="User account is inactive",
            endpoint="websocket_auth",
            user_email=user.email,
            user_id=user.id
        )
        raise AuthenticationError(
            detail="User account is inactive",
            error_code=AuthErrorCodes.USER_INACTIVE
        )
    
    # Verify user_id matches token
    if user.id != validation_result.payload.user_id:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.TOKEN_INVALID,
            detail="Token user_id does not match database user",
            endpoint="websocket_auth",
            user_email=user.email,
            user_id=user.id
        )
        raise AuthenticationError(
            detail="Invalid token user information",
            error_code=AuthErrorCodes.TOKEN_INVALID
        )
    
    # Verify client_id matches if user has a client
    token_client_id = validation_result.payload.client_id
    if user.client_id and token_client_id != user.client_id:
        AuthLogger.log_auth_failure(
            error_code=AuthErrorCodes.CLIENT_NOT_FOUND,
            detail="Token client_id does not match user's client",
            endpoint="websocket_auth",
            user_email=user.email,
            user_id=user.id,
            client_id=user.client_id
        )
        raise AuthenticationError(
            detail="Invalid client information in token",
            error_code=AuthErrorCodes.CLIENT_NOT_FOUND
        )
    
    # Log successful authentication
    AuthLogger.log_auth_success(
        user_email=user.email,
        client_id=token_client_id,
        endpoint="websocket_auth",
        user_id=user.id
    )
    
    return user, token_client_id


