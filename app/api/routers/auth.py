from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    verify_token, get_token_info, AuthLogger
)
from app.db.session import get_db
from app.models.user import User
from app.models.client import Client
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserOut
from app.api.deps import require_admin
from app.services.auth_analytics_service import AuthAnalyticsService
from app.middleware.security import extract_client_info

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserOut)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    client = None
    if payload.client_name:
        client = db.query(Client).filter(Client.slug == payload.client_name.lower().replace(" ", "-")).first()
        if client is None and payload.create_client_if_missing:
            client = Client(name=payload.client_name, slug=payload.client_name.lower().replace(" ", "-"))
            db.add(client)
            db.flush()

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role or "client",
        client_id=client.id if client else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # Extract client info for audit logging
    client_info = extract_client_info(request)
    
    # Validate input
    if not form_data.username or not form_data.password:
        AuthLogger.log_auth_failure(
            error_code="INVALID_INPUT",
            detail="Email and password are required",
            endpoint="login",
            **client_info
        )
        raise HTTPException(status_code=400, detail="Email and password are required")

    # Find user
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Verify user exists and check password
    if not user or not verify_password(form_data.password, user.hashed_password):
        AuthLogger.log_auth_failure(
            error_code="INVALID_CREDENTIALS",
            detail="Incorrect email or password",
            endpoint="login",
            user_email=form_data.username,
            **client_info
        )
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    # Check if user is active
    if not user.is_active:
        AuthLogger.log_auth_failure(
            error_code="USER_INACTIVE",
            detail="Account is inactive",
            endpoint="login",
            user_email=user.email,
            user_id=user.id,
            **client_info
        )
        raise HTTPException(status_code=400, detail="Account is inactive")

    # Create access token with enhanced payload
    token = create_access_token(
        user_email=user.email,
        user_id=user.id,
        client_id=user.client_id
    )
    
    # Log successful login
    AuthLogger.log_auth_success(
        user_email=user.email,
        user_id=user.id,
        client_id=user.client_id,
        endpoint="login",
        **client_info
    )
    
    return Token(access_token=token, token_type="bearer")





# Debug and Monitoring Endpoints (Admin Only)

@router.get("/debug/token-info")
def debug_token_info(
    token: str = Query(..., description="JWT token to analyze"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Debug endpoint to inspect token information (admin only)"""
    try:
        token_info = get_token_info(token)
        return {
            "status": "success",
            "token_info": token_info,
            "analyzed_by": current_user.email,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "analyzed_by": current_user.email,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }


@router.get("/debug/validate-token")
def debug_validate_token(
    test_token: str = Query(..., description="Token to validate"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Debug endpoint to test token validation (admin only)"""
    validation_result = verify_token(test_token)
    
    return {
        "is_valid": validation_result.is_valid,
        "payload": {
            "sub": validation_result.payload.sub if validation_result.payload else None,
            "user_id": validation_result.payload.user_id if validation_result.payload else None,
            "client_id": validation_result.payload.client_id if validation_result.payload else None,
            "exp": validation_result.payload.exp.isoformat() if validation_result.payload and validation_result.payload.exp else None,
            "iat": validation_result.payload.iat.isoformat() if validation_result.payload and validation_result.payload.iat else None
        } if validation_result.payload else None,
        "error": validation_result.error,
        "error_code": validation_result.error_code,
        "validated_by": current_user.email,
        "validated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/debug/user-auth-test")
def debug_user_auth_test(
    user_email: str = Query(..., description="User email to test authentication for"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Debug endpoint to test user authentication setup (admin only)"""
    
    # Find user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return {
            "status": "error",
            "error": "User not found",
            "user_email": user_email,
            "tested_by": current_user.email,
            "tested_at": datetime.now(timezone.utc).isoformat()
        }
    
    # Create a test token
    try:
        test_token = create_access_token(
            user_email=user.email,
            user_id=user.id,
            client_id=user.client_id,
            expires_minutes=5  # Short-lived test token
        )
        
        # Validate the token
        validation_result = verify_token(test_token)
        
        return {
            "status": "success",
            "user_info": {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "role": user.role,
                "client_id": user.client_id
            },
            "token_test": {
                "token_created": True,
                "token_valid": validation_result.is_valid,
                "validation_error": validation_result.error,
                "error_code": validation_result.error_code
            },
            "tested_by": current_user.email,
            "tested_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Token creation failed: {str(e)}",
            "user_email": user_email,
            "tested_by": current_user.email,
            "tested_at": datetime.now(timezone.utc).isoformat()
        }


@router.get("/analytics/statistics")
def get_auth_statistics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get authentication statistics and metrics (admin only)"""
    analytics_service = AuthAnalyticsService(db)
    stats = analytics_service.get_auth_statistics(days)
    
    return {
        "status": "success",
        "statistics": stats,
        "generated_by": current_user.email,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/analytics/user-history")
def get_user_auth_history(
    user_email: str = Query(..., description="User email to get history for"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get authentication history for a specific user (admin only)"""
    analytics_service = AuthAnalyticsService(db)
    history = analytics_service.get_user_auth_history(user_email, days)
    
    return {
        "status": "success",
        "history": history,
        "generated_by": current_user.email,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/analytics/security-alerts")
def get_security_alerts(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get security alerts based on authentication patterns (admin only)"""
    analytics_service = AuthAnalyticsService(db)
    alerts = analytics_service.get_security_alerts(hours)
    
    return {
        "status": "success",
        "alerts": alerts,
        "alert_count": len(alerts),
        "generated_by": current_user.email,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/analytics/client-stats")
def get_client_auth_stats(
    client_id: int = Query(..., description="Client ID to get statistics for"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get authentication statistics for a specific client (admin only)"""
    analytics_service = AuthAnalyticsService(db)
    stats = analytics_service.get_client_auth_stats(client_id, days)
    
    return {
        "status": "success",
        "statistics": stats,
        "generated_by": current_user.email,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/analytics/search-logs")
def search_auth_logs(
    user_email: Optional[str] = Query(None, description="Filter by user email (partial match)"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    error_code: Optional[str] = Query(None, description="Filter by error code"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Search authentication logs with various filters (admin only)"""
    
    # Parse dates if provided
    parsed_start_date = None
    parsed_end_date = None
    
    try:
        if start_date:
            parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    
    analytics_service = AuthAnalyticsService(db)
    results = analytics_service.search_auth_logs(
        user_email=user_email,
        client_id=client_id,
        event_type=event_type,
        success=success,
        error_code=error_code,
        ip_address=ip_address,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        limit=limit,
        offset=offset
    )
    
    return {
        "status": "success",
        "results": results,
        "searched_by": current_user.email,
        "searched_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/auth-system")
def auth_system_health(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get authentication system health status (admin only)"""
    
    try:
        # Test database connectivity
        db.execute("SELECT 1")
        db_status = "healthy"
        db_error = None
    except Exception as e:
        db_status = "error"
        db_error = str(e)
    
    # Test token creation and validation
    try:
        test_token = create_access_token(
            user_email="health-check@test.com",
            user_id=999999,
            client_id=None,
            expires_minutes=1
        )
        validation_result = verify_token(test_token)
        token_status = "healthy" if validation_result.is_valid else "error"
        token_error = validation_result.error if not validation_result.is_valid else None
    except Exception as e:
        token_status = "error"
        token_error = str(e)
    
    # Get recent authentication activity
    analytics_service = AuthAnalyticsService(db)
    recent_stats = analytics_service.get_auth_statistics(days=1)
    
    overall_status = "healthy"
    if db_status == "error" or token_status == "error":
        overall_status = "error"
    elif recent_stats["failure_count"] > recent_stats["success_count"]:
        overall_status = "warning"
    
    return {
        "status": overall_status,
        "components": {
            "database": {
                "status": db_status,
                "error": db_error
            },
            "token_system": {
                "status": token_status,
                "error": token_error
            },
            "recent_activity": {
                "status": "healthy" if recent_stats["total_events"] > 0 else "warning",
                "total_events_24h": recent_stats["total_events"],
                "success_rate_24h": recent_stats["success_rate"]
            }
        },
        "checked_by": current_user.email,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }