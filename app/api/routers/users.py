from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.models.client import Client
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/users")

@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)):
    return user

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: None = Depends(require_admin)):
    return db.query(User).order_by(User.id.desc()).all()

@router.post("/", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    client_id = None
    if payload.client_name:
        slug = payload.client_name.lower().replace(" ", "-")
        client = db.query(Client).filter(Client.slug == slug).first()
        if client is None:
            client = Client(name=payload.client_name, slug=slug)
            db.add(client)
            db.flush()
        client_id = client.id
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role or "client",
        client_id=client_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



