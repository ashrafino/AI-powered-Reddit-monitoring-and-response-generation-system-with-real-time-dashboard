from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.client import Client
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserOut

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
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Validate input
    if not form_data.username or not form_data.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    # Find user
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Verify user exists and check password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")

    # Create access token
    token = create_access_token(subject=user.email)
    return Token(access_token=token, token_type="bearer")



