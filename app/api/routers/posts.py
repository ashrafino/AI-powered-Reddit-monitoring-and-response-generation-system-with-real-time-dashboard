from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio

from app.api.deps import get_current_user_with_client
from app.db.session import get_db
from app.models.post import MatchedPost, AIResponse
from app.models.user import User
from app.services.openai_service import generate_reddit_replies_with_research
from app.schemas.post import PostOut, ResponseOut

router = APIRouter(prefix="/posts")

@router.get("/", response_model=List[PostOut])
def list_posts(
    db: Session = Depends(get_db), 
    user_client = Depends(get_current_user_with_client),
    limit: int = 50,
    offset: int = 0
):
    """List posts with responses for the current user/client"""
    user, user_client_id = user_client
    
    query = db.query(MatchedPost)
    
    # Filter by client if user is not admin
    if user.role != "admin":
        query = query.filter(MatchedPost.client_id == user_client_id)
    
    posts = query.order_by(MatchedPost.created_at.desc()).offset(offset).limit(limit).all()
    
    return posts

@router.post("/{post_id}/generate-response")
async def generate_response_for_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_client = Depends(get_current_user_with_client)
):
    """Generate AI response for a specific post"""
    user, user_client_id = user_client
    
    # Get the post
    post = db.query(MatchedPost).filter(MatchedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permissions
    if user.role != "admin" and post.client_id != user_client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if response already exists
    existing_response = db.query(AIResponse).filter(
        AIResponse.post_id == post_id
    ).first()
    
    if existing_response:
        return {
            "status": "exists",
            "message": "Response already exists for this post",
            "response_id": existing_response.id
        }
    
    try:
        # Generate response with research
        result = await generate_reddit_replies_with_research(
            post_title=post.title,
            post_content=post.content or "",
            num=3,
            enable_research=True
        )
        
        if result["responses"]:
            # Save the best response
            best_response = result["responses"][0]
            
            ai_response = AIResponse(
                post_id=post.id,
                client_id=post.client_id,
                content=best_response["content"],
                score=best_response["score"],
                quality_breakdown=best_response["quality_breakdown"],
                feedback=best_response["feedback"],
                grade=best_response["grade"],
                research_context=result.get("context_data", {}) if result.get("context_data") else None
            )
            
            db.add(ai_response)
            db.commit()
            db.refresh(ai_response)
            
            return {
                "status": "generated",
                "message": "Response generated successfully",
                "response": {
                    "id": ai_response.id,
                    "content": ai_response.content,
                    "score": ai_response.score,
                    "grade": ai_response.grade
                }
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to generate response",
                "error": "No responses generated"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generating response: {str(e)}"
        }

@router.post("/responses/{response_id}/copied")
def mark_response_copied(
    response_id: int,
    db: Session = Depends(get_db),
    user_client = Depends(get_current_user_with_client)
):
    """Mark a response as copied"""
    user, user_client_id = user_client
    
    response = db.query(AIResponse).filter(AIResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Check permissions
    if user.role != "admin" and response.client_id != user_client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    response.copied = True
    db.commit()
    
    return {"status": "success", "message": "Response marked as copied"}

@router.post("/responses/{response_id}/compliance")
def acknowledge_compliance(
    response_id: int,
    db: Session = Depends(get_db),
    user_client = Depends(get_current_user_with_client)
):
    """Acknowledge compliance for a response"""
    user, user_client_id = user_client
    
    response = db.query(AIResponse).filter(AIResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Check permissions
    if user.role != "admin" and response.client_id != user_client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    response.compliance_acknowledged = True
    db.commit()
    
    return {"status": "success", "message": "Compliance acknowledged"}