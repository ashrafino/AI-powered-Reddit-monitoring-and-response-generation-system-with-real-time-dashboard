from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.api.deps import get_current_user, get_db
from app.celery_app import celery_app
from sqlalchemy.orm import Session
import logging
import anyio

router = APIRouter(prefix="/ops")
logger = logging.getLogger(__name__)

def run_scan_sync(db: Session):
    """Synchronous scan function for development without Celery"""
    from app.models.config import ClientConfig
    from app.models.post import MatchedPost, AIResponse
    from app.services.reddit_service import find_matching_posts, test_reddit_connection
    from app.services.context_service import fetch_google_results, fetch_youtube_results
    from app.services.openai_service import generate_reddit_replies, generate_reddit_replies_with_research
    
    created_posts = 0
    created_responses = 0
    
    try:
        # Test Reddit connection
        connection_status = test_reddit_connection()
        if connection_status["status"] != "success":
            logger.error(f"Reddit API connection failed: {connection_status['message']}")
            return {"error": connection_status['message'], "created_posts": 0, "created_responses": 0}
        
        # Get active configs
        active_configs = db.query(ClientConfig).filter(ClientConfig.is_active == True).all()
        logger.info(f"Found {len(active_configs)} active client configurations")
        
        for cfg in active_configs:
            try:
                subs = (cfg.reddit_subreddits or "").split(",") if cfg.reddit_subreddits else []
                keys = (cfg.keywords or "").split(",") if cfg.keywords else []
                subs = [s.strip() for s in subs if s.strip()]
                keys = [k.strip() for k in keys if k.strip()]
                
                if not subs or not keys:
                    logger.warning(f"Client {cfg.client_id} has incomplete configuration")
                    continue
                
                # Get existing post IDs
                existing_ids = set(x[0] for x in db.query(MatchedPost.reddit_post_id).filter(MatchedPost.client_id == cfg.client_id).all())
                
                # Find matching posts
                matches = find_matching_posts(subs, keys, existing_ids)
                logger.info(f"Found {len(matches)} new matches for client {cfg.client_id}")
                
                for m in matches[:5]:  # Limit to 5 posts per scan for quick results
                    if m["id"] in existing_ids:
                        continue
                    
                    # Create post
                    post = MatchedPost(
                        client_id=cfg.client_id,
                        subreddit=m["subreddit"],
                        reddit_post_id=m["id"],
                        title=m["title"],
                        url=m["url"],
                        author=m["author"],
                        content=m.get("content"),
                        keywords_matched=m.get("keywords_matched"),
                        score=m.get("score", 0),
                        num_comments=m.get("num_comments", 0),
                    )
                    db.add(post)
                    db.flush()
                    created_posts += 1
                    
                    # Fetch context
                    context_text = ""
                    try:
                        google_results = anyio.run(fetch_google_results, post.title, 2)
                        youtube_results = anyio.run(fetch_youtube_results, post.title, 2)
                        context_text = "\n".join([
                            *(f"Google: {r.get('title', '')} {r.get('link', r.get('url', ''))}" for r in google_results),
                            *(f"YouTube: {r.get('title', '')} {r.get('url', '')}" for r in youtube_results),
                        ])
                    except Exception as e:
                        logger.warning(f"Context fetching failed: {e}")
                    
                    # Generate responses with subreddit guidelines
                    try:
                        # Use async version with subreddit guidelines
                        result = anyio.run(
                            generate_reddit_replies_with_research,
                            post.title,
                            post.content or "",
                            3,
                            None,
                            None,
                            True,
                            post.subreddit
                        )
                        
                        for suggestion_data in result.get("responses", []):
                            resp = AIResponse(
                                post_id=post.id,
                                client_id=cfg.client_id,
                                content=suggestion_data['content'],
                                score=suggestion_data['score'],
                                quality_breakdown=suggestion_data.get('quality_breakdown'),
                                feedback=suggestion_data.get('feedback'),
                                grade=suggestion_data.get('grade')
                            )
                            db.add(resp)
                            created_responses += 1
                    except Exception as e:
                        logger.error(f"AI response generation failed: {e}")
                    
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Error processing client {cfg.client_id}: {e}")
                db.rollback()
                continue
        
        return {"created_posts": created_posts, "created_responses": created_responses}
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        db.rollback()
        return {"error": str(e), "created_posts": created_posts, "created_responses": created_responses}

@router.post("/scan")
def manual_scan(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(get_current_user)
):
    """
    Trigger a Reddit scan. 
    - Tries Celery first (production)
    - Falls back to synchronous scan (development)
    """
    try:
        # Try Celery first
        celery_app.send_task("app.tasks.reddit_tasks.scan_reddit")
        return {"status": "enqueued", "method": "celery"}
    except Exception as celery_error:
        logger.warning(f"Celery unavailable, running synchronous scan: {celery_error}")
        
        # Fallback to synchronous scan
        try:
            result = run_scan_sync(db)
            return {
                "status": "completed", 
                "method": "sync",
                "created_posts": result.get("created_posts", 0),
                "created_responses": result.get("created_responses", 0),
                "error": result.get("error")
            }
        except Exception as sync_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scan failed: {str(sync_error)}",
            )



