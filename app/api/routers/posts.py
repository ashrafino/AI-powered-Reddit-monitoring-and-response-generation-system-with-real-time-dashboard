from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.post import MatchedPost, AIResponse
from app.schemas.post import MatchedPostOut, AIResponseOut

router = APIRouter(prefix="/posts")

@router.get("/", response_model=list[MatchedPostOut])
def list_posts(db: Session = Depends(get_db), user = Depends(get_current_user)):
    q = db.query(MatchedPost)
    if user.role != "admin":
        q = q.filter(MatchedPost.client_id == user.client_id)
    # Optimize: Use eager loading for responses to avoid N+1 queries
    return q.options(
        joinedload(MatchedPost.responses)
    ).order_by(MatchedPost.id.desc()).limit(100).all()

@router.post("/{post_id}/review")
def mark_reviewed(post_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    post = db.query(MatchedPost).filter(MatchedPost.id == post_id).first()
    if not post or (user.role != "admin" and post.client_id != user.client_id):
        raise HTTPException(status_code=404, detail="Post not found")
    post.reviewed = True
    db.commit()
    return {"status": "ok"}

@router.post("/{post_id}/flag")
def mark_flag(post_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    post = db.query(MatchedPost).filter(MatchedPost.id == post_id).first()
    if not post or (user.role != "admin" and post.client_id != user.client_id):
        raise HTTPException(status_code=404, detail="Post not found")
    post.flagged = True
    db.commit()
    return {"status": "ok"}

@router.post("/responses/{response_id}/copied", response_model=AIResponseOut)
def mark_copied(response_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    resp = db.query(AIResponse).filter(AIResponse.id == response_id).first()
    if not resp or (user.role != "admin" and resp.client_id != user.client_id):
        raise HTTPException(status_code=404, detail="Response not found")
    resp.copied = True
    db.commit()
    db.refresh(resp)
    return resp

@router.post("/responses/{response_id}/compliance", response_model=AIResponseOut)
def mark_compliance(response_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    resp = db.query(AIResponse).filter(AIResponse.id == response_id).first()
    if not resp or (user.role != "admin" and resp.client_id != user.client_id):
        raise HTTPException(status_code=404, detail="Response not found")
    resp.compliance_ack = True
    db.commit()
    db.refresh(resp)
    return resp


