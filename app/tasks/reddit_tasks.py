from typing import List
import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.config import ClientConfig
from app.models.post import MatchedPost, AIResponse
from app.models.analytics import AnalyticsEvent
from app.services.reddit_service import find_matching_posts, RedditAPIError, test_reddit_connection
from app.services.context_service import fetch_google_results, fetch_youtube_results
from app.services.openai_service import generate_reddit_replies
from app.services.email_service import send_email
from app.services.websocket_service import WebSocketNotifier
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.reddit_tasks.scan_reddit", bind=True, max_retries=3)
def scan_reddit(self):
    """Enhanced Reddit scanning with comprehensive error handling and real-time updates"""
    db: Session = SessionLocal()
    created_posts: int = 0
    created_responses: int = 0
    errors: List[str] = []
    scan_start_time = datetime.utcnow()
    
    try:
        logger.info("Starting Reddit scan")
        
        # Test Reddit connection first
        connection_status = test_reddit_connection()
        if connection_status["status"] != "success":
            error_msg = f"Reddit API connection failed: {connection_status['message']}"
            logger.error(error_msg)
            
            # Notify all clients about the connection issue
            try:
                asyncio.run(WebSocketNotifier.notify_system_status("error", error_msg))
            except Exception as e:
                logger.error(f"Failed to send system status notification: {e}")
            
            # Retry with exponential backoff
            raise self.retry(exc=RedditAPIError(error_msg), countdown=60 * (2 ** self.request.retries))
        
        # Notify scan started
        try:
            asyncio.run(WebSocketNotifier.notify_scan_started())
        except Exception as e:
            logger.warning(f"Failed to send scan started notification: {e}")
        
        active_configs: List[ClientConfig] = db.query(ClientConfig).filter(ClientConfig.is_active == True).all()
        logger.info(f"Found {len(active_configs)} active client configurations")
        
        for cfg in active_configs:
            client_start_time = datetime.utcnow()
            client_posts = 0
            client_responses = 0
            
            try:
                # Notify client-specific scan started
                asyncio.run(WebSocketNotifier.notify_scan_started(cfg.client_id))
                
                # Parse and validate configuration
                subs = (cfg.reddit_subreddits or "").split(",") if cfg.reddit_subreddits else []
                keys = (cfg.keywords or "").split(",") if cfg.keywords else []
                subs = [s.strip() for s in subs if s.strip()]
                keys = [k.strip() for k in keys if k.strip()]
                
                if not subs or not keys:
                    logger.warning(f"Client {cfg.client_id} has incomplete configuration (subs: {len(subs)}, keys: {len(keys)})")
                    continue

                logger.info(f"Scanning for client {cfg.client_id}: {len(subs)} subreddits, {len(keys)} keywords")

                # Optimize: Only fetch post IDs, not full objects
                existing_ids = set(x[0] for x in db.query(MatchedPost.reddit_post_id).filter(MatchedPost.client_id == cfg.client_id).all())
                logger.debug(f"Client {cfg.client_id} has {len(existing_ids)} existing posts")
                
                # Find matching posts with enhanced error handling
                try:
                    matches = find_matching_posts(subs, keys, existing_ids)
                    logger.info(f"Found {len(matches)} new matches for client {cfg.client_id}")
                    
                except RedditAPIError as e:
                    error_msg = f"Reddit API error for client {cfg.client_id}: {e.message}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
                    # Notify client about the error
                    try:
                        asyncio.run(WebSocketNotifier.notify_scan_completed(cfg.client_id, {
                            "status": "error",
                            "message": error_msg,
                            "posts_created": 0,
                            "responses_created": 0
                        }))
                    except Exception:
                        pass
                    
                    continue
                
                # Process each match
                for m in matches:
                    try:
                        if m["id"] in existing_ids:
                            continue
                            
                        # Create post record
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
                        client_posts += 1

                        # Send immediate notification about new post
                        try:
                            asyncio.run(WebSocketNotifier.notify_new_post(cfg.client_id, {
                                "id": post.id,
                                "title": post.title,
                                "subreddit": post.subreddit,
                                "url": post.url,
                                "keywords_matched": post.keywords_matched,
                                "score": post.score,
                                "num_comments": post.num_comments,
                                "author": post.author,
                                "created_at": post.created_at.isoformat() if post.created_at else None
                            }))
                        except Exception as e:
                            logger.warning(f"Failed to send new post notification: {e}")

                        # Fetch context with error handling
                        context_text = ""
                        try:
                            import anyio
                            google_results = anyio.run(fetch_google_results, post.title, 3)
                            youtube_results = anyio.run(fetch_youtube_results, post.title, 3)
                            
                            context_text = "\n".join([
                                *(f"Google: {r.get('title', '')} {r.get('link', r.get('url', ''))}" for r in google_results),
                                *(f"YouTube: {r.get('title', '')} {r.get('url', '')}" for r in youtube_results),
                            ])
                        except Exception as e:
                            logger.warning(f"Context fetching failed for post {post.id}: {e}")

                        # Generate responses with quality scoring
                        try:
                            suggestions = generate_reddit_replies(
                                prompt=post.title, 
                                context=context_text, 
                                num=3
                            )
                            
                            for suggestion_data in suggestions:
                                resp = AIResponse(
                                    post_id=post.id,
                                    client_id=cfg.client_id,
                                    content=suggestion_data['content'],
                                    score=suggestion_data['score'],
                                )
                                db.add(resp)
                                created_responses += 1
                                client_responses += 1

                                # Send immediate notification about new response
                                try:
                                    asyncio.run(WebSocketNotifier.notify_new_response(cfg.client_id, {
                                        "id": resp.id,
                                        "post_id": post.id,
                                        "content": suggestion_data['content'],
                                        "score": suggestion_data['score'],
                                        "quality_breakdown": suggestion_data.get('quality_breakdown', {}),
                                        "created_at": resp.created_at.isoformat() if resp.created_at else None
                                    }))
                                except Exception as e:
                                    logger.warning(f"Failed to send new response notification: {e}")
                                    
                        except Exception as e:
                            logger.error(f"AI response generation failed for post {post.id}: {e}")
                            errors.append(f"AI response generation failed: {e}")

                        # Track analytics
                        try:
                            analytics_service = AnalyticsService(db)
                            analytics_service.track_event(cfg.client_id, "post_matched", {"post_id": post.id})
                        except Exception as e:
                            logger.warning(f"Analytics tracking failed for post {post.id}: {e}")

                        db.commit()
                        
                    except Exception as e:
                        logger.error(f"Error processing match {m.get('id', 'unknown')}: {e}")
                        errors.append(f"Error processing match: {e}")
                        db.rollback()
                        continue

                # Send client scan completion notification
                client_duration = (datetime.utcnow() - client_start_time).total_seconds()
                try:
                    asyncio.run(WebSocketNotifier.notify_scan_completed(cfg.client_id, {
                        "status": "success",
                        "posts_created": client_posts,
                        "responses_created": client_responses,
                        "duration_seconds": client_duration,
                        "errors": len([e for e in errors if f"client {cfg.client_id}" in e])
                    }))
                except Exception as e:
                    logger.warning(f"Failed to send scan completion notification: {e}")
                    
            except Exception as e:
                error_msg = f"Error processing client {cfg.client_id}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                
                # Notify client about error
                try:
                    asyncio.run(WebSocketNotifier.notify_scan_completed(cfg.client_id, {
                        "status": "error",
                        "message": str(e),
                        "posts_created": client_posts,
                        "responses_created": client_responses
                    }))
                except Exception:
                    pass
                
                continue

        # Send overall scan completion notification
        scan_duration = (datetime.utcnow() - scan_start_time).total_seconds()
        try:
            asyncio.run(WebSocketNotifier.notify_system_status("success", 
                f"Reddit scan completed: {created_posts} posts, {created_responses} responses in {scan_duration:.1f}s"))
        except Exception as e:
            logger.warning(f"Failed to send system status notification: {e}")
            
    except RedditAPIError as e:
        logger.error(f"Reddit API error during scan: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        
    except Exception as e:
        logger.error(f"Unexpected error during Reddit scan: {e}")
        errors.append(f"Unexpected error: {e}")
        
        # Send error notification
        try:
            asyncio.run(WebSocketNotifier.notify_system_status("error", f"Reddit scan failed: {e}"))
        except Exception:
            pass
            
    finally:
        db.close()

    result = {
        "created_posts": created_posts,
        "created_responses": created_responses,
        "errors": errors,
        "scan_duration": (datetime.utcnow() - scan_start_time).total_seconds()
    }
    
    logger.info(f"Reddit scan completed: {result}")
    return result

@celery_app.task(name="app.tasks.reddit_tasks.update_performance_metrics")
def update_performance_metrics():
    """Update daily performance metrics for all clients"""
    db: Session = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        
        # Get all active clients
        active_configs = db.query(ClientConfig).filter(ClientConfig.is_active == True).all()
        client_ids = list(set(cfg.client_id for cfg in active_configs))
        
        updated_clients = 0
        for client_id in client_ids:
            try:
                analytics_service.update_performance_metrics(client_id)
                updated_clients += 1
                
                # Send analytics update notification
                summary = analytics_service.get_dashboard_summary(client_id)
                asyncio.run(WebSocketNotifier.notify_analytics_update(client_id, summary))
                
            except Exception as e:
                print(f"Error updating metrics for client {client_id}: {e}")
        
        return {"updated_clients": updated_clients}
        
    finally:
        db.close()


@celery_app.task(name="app.tasks.reddit_tasks.generate_trend_analysis")
def generate_trend_analysis():
    """Generate weekly trend analysis for all clients"""
    db: Session = SessionLocal()
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, and_
        from app.models.analytics import TrendAnalysis
        
        # Get data for the past week
        week_start = datetime.utcnow() - timedelta(days=7)
        
        # Get all active clients
        active_configs = db.query(ClientConfig).filter(ClientConfig.is_active == True).all()
        client_ids = list(set(cfg.client_id for cfg in active_configs))
        
        trends_created = 0
        
        for client_id in client_ids:
            try:
                # Analyze keyword trends
                keyword_activity = db.query(
                    MatchedPost.keywords_matched,
                    func.count(MatchedPost.id).label('count'),
                    func.avg(MatchedPost.score).label('avg_score'),
                    func.avg(MatchedPost.num_comments).label('avg_comments')
                ).filter(
                    and_(
                        MatchedPost.client_id == client_id,
                        MatchedPost.created_at >= week_start
                    )
                ).group_by(MatchedPost.keywords_matched).all()
                
                # Analyze subreddit trends
                subreddit_activity = db.query(
                    MatchedPost.subreddit,
                    func.count(MatchedPost.id).label('count'),
                    func.avg(MatchedPost.score).label('avg_score')
                ).filter(
                    and_(
                        MatchedPost.client_id == client_id,
                        MatchedPost.created_at >= week_start
                    )
                ).group_by(MatchedPost.subreddit).all()
                
                # Create trend analysis entries
                for keywords, count, avg_score, avg_comments in keyword_activity:
                    if not keywords or count < 3:  # Skip low-activity keywords
                        continue
                    
                    activity_score = (count * 10) + (float(avg_score or 0) / 10) + (float(avg_comments or 0) / 5)
                    
                    # Calculate growth rate (simplified - would need historical data for accurate calculation)
                    growth_rate = min(100, max(-100, (count - 5) * 10))  # Placeholder calculation
                    
                    trend = TrendAnalysis(
                        client_id=client_id,
                        topic=keywords,
                        keywords=keywords.split(','),
                        subreddits=[sub for sub, _, _ in subreddit_activity if sub],
                        activity_score=activity_score,
                        growth_rate=growth_rate,
                        sentiment_score=min(100, max(0, float(avg_score or 0) * 2)),  # Simplified sentiment
                        week_start=week_start
                    )
                    
                    db.add(trend)
                    trends_created += 1
                
                db.commit()
                
            except Exception as e:
                print(f"Error generating trends for client {client_id}: {e}")
                db.rollback()
        
        return {"trends_created": trends_created}
        
    finally:
        db.close()


@celery_app.task(name="app.tasks.reddit_tasks.cleanup_old_data")
def cleanup_old_data():
    """Clean up old data to maintain database performance"""
    db: Session = SessionLocal()
    try:
        from datetime import datetime, timedelta
        
        # Delete analytics events older than 90 days
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        old_events = db.query(AnalyticsEvent).filter(AnalyticsEvent.created_at < ninety_days_ago)
        events_deleted = old_events.count()
        old_events.delete()
        
        # Delete performance metrics older than 180 days
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        from app.models.analytics import PerformanceMetrics
        old_metrics = db.query(PerformanceMetrics).filter(PerformanceMetrics.created_at < six_months_ago)
        metrics_deleted = old_metrics.count()
        old_metrics.delete()
        
        # Delete trend analysis older than 1 year
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        from app.models.analytics import TrendAnalysis
        old_trends = db.query(TrendAnalysis).filter(TrendAnalysis.created_at < one_year_ago)
        trends_deleted = old_trends.count()
        old_trends.delete()
        
        db.commit()
        
        return {
            "events_deleted": events_deleted,
            "metrics_deleted": metrics_deleted,
            "trends_deleted": trends_deleted
        }
        
    finally:
        db.close()