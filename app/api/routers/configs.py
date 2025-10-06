from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.api.deps import get_current_user, get_current_user_with_client
from app.db.session import get_db
from app.models.config import ClientConfig
from app.schemas.config import ClientConfigCreate, ClientConfigOut, ClientConfigUpdate

router = APIRouter(prefix="/configs")


def list_to_csv(values: List[str] | None) -> str | None:
    if values is None:
        return None
    return ",".join([v.strip() for v in values if v and v.strip()])


@router.post("/", response_model=ClientConfigOut)
def create_config(payload: ClientConfigCreate, db: Session = Depends(get_db), user_client = Depends(get_current_user_with_client)):
    from app.models.client import Client
    
    user, user_client_id = user_client
    # client users can only create for their own client
    if user.role != "admin" and payload.client_id != user_client_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Validate that the client exists
    client = db.query(Client).filter(Client.id == payload.client_id).first()
    if not client:
        raise HTTPException(
            status_code=400, 
            detail=f"Client with ID {payload.client_id} does not exist. Please create the client first or use an existing client ID."
        )
    
    try:
        config = ClientConfig(
            client_id=payload.client_id,
            reddit_username=payload.reddit_username,
            reddit_subreddits=list_to_csv(payload.reddit_subreddits),
            keywords=list_to_csv(payload.keywords),
            is_active=payload.is_active,
            scan_interval_minutes=payload.scan_interval_minutes or 5,
            scan_start_hour=payload.scan_start_hour or 0,
            scan_end_hour=payload.scan_end_hour or 23,
            scan_days=payload.scan_days or "1,2,3,4,5,6,7",
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        
        # Convert back to list format for response
        config.reddit_subreddits = payload.reddit_subreddits
        config.keywords = payload.keywords
        return config
    except Exception as e:
        db.rollback()
        # Log the actual error for debugging
        print(f"Error creating config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create configuration: {str(e)}"
        )

@router.get("/", response_model=list[ClientConfigOut])
def list_configs(db: Session = Depends(get_db), user_client = Depends(get_current_user_with_client)):
    user, user_client_id = user_client
    q = db.query(ClientConfig).options(joinedload(ClientConfig.client))
    if user.role != "admin":
        q = q.filter(ClientConfig.client_id == user_client_id)
    configs = q.order_by(ClientConfig.id.desc()).all()
    
    # Convert CSV strings back to lists for response
    for config in configs:
        config.reddit_subreddits = config.reddit_subreddits.split(",") if config.reddit_subreddits else []
        config.keywords = config.keywords.split(",") if config.keywords else []
    
    return configs


@router.put("/{config_id}", response_model=ClientConfigOut)
def update_config(config_id: int, payload: ClientConfigUpdate, db: Session = Depends(get_db), user_client = Depends(get_current_user_with_client)):
    user, user_client_id = user_client
    config = db.query(ClientConfig).filter(ClientConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role != "admin" and config.client_id != user_client_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if payload.client_id is not None:
        if user.role != "admin" and payload.client_id != user_client_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        config.client_id = payload.client_id

    if payload.reddit_username is not None:
        config.reddit_username = payload.reddit_username
    if payload.reddit_subreddits is not None:
        config.reddit_subreddits = list_to_csv(payload.reddit_subreddits)
    if payload.keywords is not None:
        config.keywords = list_to_csv(payload.keywords)
    if payload.is_active is not None:
        config.is_active = payload.is_active
    if payload.scan_interval_minutes is not None:
        config.scan_interval_minutes = payload.scan_interval_minutes
    if payload.scan_start_hour is not None:
        config.scan_start_hour = payload.scan_start_hour
    if payload.scan_end_hour is not None:
        config.scan_end_hour = payload.scan_end_hour
    if payload.scan_days is not None:
        config.scan_days = payload.scan_days

    db.add(config)
    db.commit()
    db.refresh(config)

    # Convert back to list format for response
    config.reddit_subreddits = config.reddit_subreddits.split(",") if config.reddit_subreddits else []
    config.keywords = config.keywords.split(",") if config.keywords else []
    return config


@router.delete("/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db), user_client = Depends(get_current_user_with_client)):
    user, user_client_id = user_client
    config = db.query(ClientConfig).filter(ClientConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role != "admin" and config.client_id != user_client_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(config)
    db.commit()
    return {"ok": True}

