from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.analytics import AnalyticsEvent, PerformanceMetrics, TrendAnalysis
from app.models.post import MatchedPost, AIResponse
from app.models.config import ClientConfig


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def track_event(self, client_id: int, event_type: str, data: Optional[Dict] = None):
        """Track an analytics event"""
        event = AnalyticsEvent(
            client_id=client_id,
            event_type=event_type,
            data=data or {}
        )
        self.db.add(event)
        self.db.commit()

    def get_dashboard_summary(self, client_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard summary for a client"""
        # Basic counts
        posts_count = self.db.query(MatchedPost).filter(MatchedPost.client_id == client_id).count()
        responses_count = self.db.query(AIResponse).filter(AIResponse.client_id == client_id).count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_posts = self.db.query(MatchedPost).filter(
            and_(MatchedPost.client_id == client_id, MatchedPost.created_at >= week_ago)
        ).count()
        
        # Response effectiveness
        copied_responses = self.db.query(AIResponse).filter(
            and_(AIResponse.client_id == client_id, AIResponse.copied == True)
        ).count()
        
        copy_rate = (copied_responses / responses_count * 100) if responses_count > 0 else 0
        
        # Top performing keywords (last 30 days)
        month_ago = datetime.utcnow() - timedelta(days=30)
        keyword_performance = self.db.query(
            MatchedPost.keywords_matched,
            func.count(MatchedPost.id).label('count')
        ).filter(
            and_(MatchedPost.client_id == client_id, MatchedPost.created_at >= month_ago)
        ).group_by(MatchedPost.keywords_matched).order_by(desc('count')).limit(5).all()
        
        # Top subreddits
        subreddit_performance = self.db.query(
            MatchedPost.subreddit,
            func.count(MatchedPost.id).label('count'),
            func.avg(MatchedPost.score).label('avg_score')
        ).filter(
            and_(MatchedPost.client_id == client_id, MatchedPost.created_at >= month_ago)
        ).group_by(MatchedPost.subreddit).order_by(desc('count')).limit(5).all()
        
        # Daily activity for the last 30 days
        daily_activity = self.db.query(
            func.date(MatchedPost.created_at).label('date'),
            func.count(MatchedPost.id).label('posts'),
            func.count(AIResponse.id).label('responses')
        ).outerjoin(AIResponse, MatchedPost.id == AIResponse.post_id).filter(
            and_(MatchedPost.client_id == client_id, MatchedPost.created_at >= month_ago)
        ).group_by(func.date(MatchedPost.created_at)).order_by('date').all()

        return {
            'posts': posts_count,
            'responses': responses_count,
            'recent_posts': recent_posts,
            'copy_rate': round(copy_rate, 1),
            'top_keywords': [{'keyword': kw, 'count': count} for kw, count in keyword_performance],
            'top_subreddits': [
                {'subreddit': sub, 'count': count, 'avg_score': round(float(avg_score or 0), 1)} 
                for sub, count, avg_score in subreddit_performance
            ],
            'daily_activity': [
                {'date': str(date), 'posts': posts or 0, 'responses': responses or 0}
                for date, posts, responses in daily_activity
            ]
        }

    def get_performance_trends(self, client_id: int, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over time"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Weekly performance comparison
        current_week = datetime.utcnow() - timedelta(days=7)
        previous_week = datetime.utcnow() - timedelta(days=14)
        
        current_week_posts = self.db.query(MatchedPost).filter(
            and_(MatchedPost.client_id == client_id, MatchedPost.created_at >= current_week)
        ).count()
        
        previous_week_posts = self.db.query(MatchedPost).filter(
            and_(
                MatchedPost.client_id == client_id, 
                MatchedPost.created_at >= previous_week,
                MatchedPost.created_at < current_week
            )
        ).count()
        
        growth_rate = 0
        if previous_week_posts > 0:
            growth_rate = ((current_week_posts - previous_week_posts) / previous_week_posts) * 100
        
        # Response quality trends
        avg_quality = self.db.query(func.avg(AIResponse.score)).filter(
            and_(AIResponse.client_id == client_id, AIResponse.created_at >= start_date)
        ).scalar() or 0
        
        return {
            'growth_rate': round(growth_rate, 1),
            'avg_response_quality': round(float(avg_quality), 1),
            'current_week_posts': current_week_posts,
            'previous_week_posts': previous_week_posts
        }

    def generate_keyword_insights(self, client_id: int) -> List[Dict[str, Any]]:
        """Generate insights about keyword performance"""
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get keyword performance with engagement metrics
        keyword_stats = self.db.query(
            MatchedPost.keywords_matched,
            func.count(MatchedPost.id).label('matches'),
            func.avg(MatchedPost.score).label('avg_score'),
            func.avg(MatchedPost.num_comments).label('avg_comments'),
            func.count(AIResponse.id).label('responses_generated')
        ).outerjoin(AIResponse, MatchedPost.id == AIResponse.post_id).filter(
            and_(MatchedPost.client_id == client_id, MatchedPost.created_at >= month_ago)
        ).group_by(MatchedPost.keywords_matched).all()
        
        insights = []
        for kw, matches, avg_score, avg_comments, responses in keyword_stats:
            if not kw:
                continue
                
            engagement_score = (float(avg_score or 0) + float(avg_comments or 0) * 2) / 3
            response_rate = (responses / matches * 100) if matches > 0 else 0
            
            # Determine performance category
            if engagement_score > 50 and response_rate > 80:
                category = "high_performer"
            elif engagement_score > 20 and response_rate > 50:
                category = "moderate_performer"
            else:
                category = "low_performer"
            
            insights.append({
                'keyword': kw,
                'matches': matches,
                'avg_engagement': round(engagement_score, 1),
                'response_rate': round(response_rate, 1),
                'category': category,
                'recommendation': self._get_keyword_recommendation(category, engagement_score, response_rate)
            })
        
        return sorted(insights, key=lambda x: x['avg_engagement'], reverse=True)

    def _get_keyword_recommendation(self, category: str, engagement: float, response_rate: float) -> str:
        """Generate recommendations based on keyword performance"""
        if category == "high_performer":
            return "Excellent performance! Consider expanding with related keywords."
        elif category == "moderate_performer":
            if response_rate < 70:
                return "Good engagement but low response rate. Review AI response quality."
            else:
                return "Solid performance. Monitor for trending topics in this area."
        else:
            if engagement < 10:
                return "Low engagement. Consider removing or refining this keyword."
            else:
                return "Moderate engagement but needs improvement. Try more specific variations."

    def update_performance_metrics(self, client_id: int):
        """Update daily performance metrics for a client"""
        today = datetime.utcnow().date()
        
        # Get today's data
        today_posts = self.db.query(MatchedPost).filter(
            and_(
                MatchedPost.client_id == client_id,
                func.date(MatchedPost.created_at) == today
            )
        ).all()
        
        # Group by keyword and subreddit
        metrics_data = {}
        
        for post in today_posts:
            keywords = (post.keywords_matched or '').split(',')
            subreddit = post.subreddit or 'unknown'
            
            for keyword in keywords:
                keyword = keyword.strip()
                if not keyword:
                    continue
                    
                key = (keyword, subreddit)
                if key not in metrics_data:
                    metrics_data[key] = {
                        'posts_matched': 0,
                        'responses_generated': 0,
                        'responses_copied': 0,
                        'total_engagement': 0,
                        'total_quality': 0,
                        'quality_count': 0
                    }
                
                metrics_data[key]['posts_matched'] += 1
                metrics_data[key]['total_engagement'] += (post.score or 0) + (post.num_comments or 0)
                
                # Count responses for this post
                responses = self.db.query(AIResponse).filter(AIResponse.post_id == post.id).all()
                metrics_data[key]['responses_generated'] += len(responses)
                metrics_data[key]['responses_copied'] += sum(1 for r in responses if r.copied)
                
                # Average quality
                for response in responses:
                    if response.score:
                        metrics_data[key]['total_quality'] += response.score
                        metrics_data[key]['quality_count'] += 1
        
        # Save or update metrics
        for (keyword, subreddit), data in metrics_data.items():
            avg_quality = data['total_quality'] / data['quality_count'] if data['quality_count'] > 0 else 0
            avg_engagement = data['total_engagement'] / data['posts_matched'] if data['posts_matched'] > 0 else 0
            
            # Check if metric already exists
            existing = self.db.query(PerformanceMetrics).filter(
                and_(
                    PerformanceMetrics.client_id == client_id,
                    PerformanceMetrics.keyword == keyword,
                    PerformanceMetrics.subreddit == subreddit,
                    func.date(PerformanceMetrics.date) == today
                )
            ).first()
            
            if existing:
                existing.posts_matched = data['posts_matched']
                existing.responses_generated = data['responses_generated']
                existing.responses_copied = data['responses_copied']
                existing.avg_response_quality = avg_quality
                existing.avg_post_engagement = avg_engagement
                existing.updated_at = datetime.utcnow()
            else:
                metric = PerformanceMetrics(
                    client_id=client_id,
                    keyword=keyword,
                    subreddit=subreddit,
                    posts_matched=data['posts_matched'],
                    responses_generated=data['responses_generated'],
                    responses_copied=data['responses_copied'],
                    avg_response_quality=avg_quality,
                    avg_post_engagement=avg_engagement,
                    date=datetime.utcnow(),
                    period_type='daily'
                )
                self.db.add(metric)
        
        self.db.commit()