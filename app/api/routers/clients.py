from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientOut

router = APIRouter(prefix="/clients")

@router.post("/", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    slug = payload.name.lower().replace(" ", "-")
    existing = db.query(Client).filter(Client.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client already exists")
    client = Client(name=payload.name, slug=slug)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("/", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db), _: None = Depends(require_admin)):
    return db.query(Client).order_by(Client.id.desc()).all()



