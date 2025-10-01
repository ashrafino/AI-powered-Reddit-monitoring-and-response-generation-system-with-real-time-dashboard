#!/usr/bin/env python3
"""
Enhanced Reddit Bot System Monitor
Monitors system health, performance, and provides diagnostics
"""

import asyncio
import json
import time
import psutil
import requests
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.models.analytics import AnalyticsEvent, PerformanceMetrics
    from app.models.post import MatchedPost, AIResponse
    from app.models.client import Client
    from app.models.config import ClientConfig
    from sqlalchemy import func
except ImportError as e:
    print(f"Warning: Could not import app modules: {e}")
    print("Running in standalone mode with limited functionality")
    settings = None


class SystemMonitor:
    def __init__(self):
        self.api_base = "http://localhost/api"
        self.redis_client = None
        self.db = None
        
        # Initialize connections
        self._init_redis()
        self._init_db()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            if settings:
                self.redis_client = redis.from_url(settings.redis_url)
                self.redis_client.ping()
                print("✅ Redis connection established")
            else:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
                self.redis_client.ping()
                print("✅ Redis connection established (default config)")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
    
    def _init_db(self):
        """Initialize database connection"""
        try:
            if settings:
                self.db = SessionLocal()
                # Test connection
                self.db.execute("SELECT 1")
                print("✅ Database connection established")
            else:
                print("⚠️  Database connection not available (app modules not imported)")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_usage": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "warning"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_docker_services(self) -> Dict[str, Any]:
        """Check Docker service status"""
        try:
            import subprocess
            
            # Get running containers
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            if result.returncode != 0:
                return {"error": "Docker Compose not available", "status": "error"}
            
            services = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        service = json.loads(line)
                        services.append({
                            "name": service.get("Service", "unknown"),
                            "state": service.get("State", "unknown"),
                            "status": service.get("Status", "unknown"),
                            "healthy": service.get("State") == "running"
                        })
                    except json.JSONDecodeError:
                        continue
            
            healthy_count = sum(1 for s in services if s["healthy"])
            total_count = len(services)
            
            return {
                "services": services,
                "healthy_services": healthy_count,
                "total_services": total_count,
                "status": "healthy" if healthy_count == total_count else "warning"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check API endpoint health"""
        try:
            # Test health endpoint
            response = requests.get(f"{self.api_base}/health", timeout=10)
            health_status = response.status_code == 200
            
            # Test WebSocket stats endpoint
            ws_response = requests.get(f"{self.api_base}/ws/stats", timeout=10)
            ws_status = ws_response.status_code == 200
            
            return {
                "health_endpoint": health_status,
                "websocket_endpoint": ws_status,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "status": "healthy" if health_status and ws_status else "warning"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health and performance"""
        if not self.redis_client:
            return {"error": "Redis not connected", "status": "error"}
        
        try:
            # Basic connectivity
            ping_result = self.redis_client.ping()
            
            # Get Redis info
            info = self.redis_client.info()
            
            # Check memory usage
            memory_usage = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            memory_percent = (memory_usage / max_memory * 100) if max_memory > 0 else 0
            
            # Check connected clients
            connected_clients = info.get('connected_clients', 0)
            
            return {
                "ping": ping_result,
                "memory_usage_mb": memory_usage / (1024**2),
                "memory_percent": memory_percent,
                "connected_clients": connected_clients,
                "uptime_seconds": info.get('uptime_in_seconds', 0),
                "status": "healthy" if ping_result and memory_percent < 80 else "warning"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health and performance"""
        if not self.db:
            return {"error": "Database not connected", "status": "error"}
        
        try:
            # Basic connectivity
            self.db.execute("SELECT 1")
            
            # Get table counts
            clients_count = self.db.query(Client).count()
            posts_count = self.db.query(MatchedPost).count()
            responses_count = self.db.query(AIResponse).count()
            configs_count = self.db.query(ClientConfig).count()
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_posts = self.db.query(MatchedPost).filter(
                MatchedPost.created_at >= yesterday
            ).count()
            
            recent_responses = self.db.query(AIResponse).filter(
                AIResponse.created_at >= yesterday
            ).count()
            
            return {
                "connectivity": True,
                "clients": clients_count,
                "total_posts": posts_count,
                "total_responses": responses_count,
                "active_configs": configs_count,
                "recent_posts_24h": recent_posts,
                "recent_responses_24h": recent_responses,
                "status": "healthy"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_celery_health(self) -> Dict[str, Any]:
        """Check Celery worker and beat health"""
        if not self.redis_client:
            return {"error": "Redis not available for Celery check", "status": "error"}
        
        try:
            # Check active workers
            from celery import Celery
            
            if settings:
                celery_app = Celery(
                    "redditbot",
                    broker=settings.celery_broker_url,
                    backend=settings.celery_result_backend,
                )
            else:
                celery_app = Celery(
                    "redditbot",
                    broker="redis://localhost:6379/1",
                    backend="redis://localhost:6379/2",
                )
            
            # Get active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            stats = inspect.stats()
            
            worker_count = len(active_workers) if active_workers else 0
            
            # Check recent task execution
            recent_tasks = 0
            if stats:
                for worker_stats in stats.values():
                    recent_tasks += worker_stats.get('total', {}).get('tasks.reddit_tasks.scan_reddit', 0)
            
            return {
                "active_workers": worker_count,
                "worker_details": active_workers or {},
                "recent_scan_tasks": recent_tasks,
                "status": "healthy" if worker_count > 0 else "warning"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from the last 24 hours"""
        if not self.db:
            return {"error": "Database not available", "status": "error"}
        
        try:
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            # Get analytics events
            events = self.db.query(
                AnalyticsEvent.event_type,
                func.count(AnalyticsEvent.id).label('count')
            ).filter(
                AnalyticsEvent.created_at >= yesterday
            ).group_by(AnalyticsEvent.event_type).all()
            
            event_counts = {event_type: count for event_type, count in events}
            
            # Get average response quality
            avg_quality = self.db.query(func.avg(AIResponse.score)).filter(
                AIResponse.created_at >= yesterday
            ).scalar() or 0
            
            # Get top performing keywords
            top_keywords = self.db.query(
                MatchedPost.keywords_matched,
                func.count(MatchedPost.id).label('count')
            ).filter(
                MatchedPost.created_at >= yesterday
            ).group_by(MatchedPost.keywords_matched).order_by(
                func.count(MatchedPost.id).desc()
            ).limit(5).all()
            
            return {
                "events_24h": event_counts,
                "avg_response_quality": round(float(avg_quality), 2),
                "top_keywords": [
                    {"keyword": kw, "matches": count} 
                    for kw, count in top_keywords if kw
                ],
                "status": "healthy"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def run_full_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        print("🔍 Running comprehensive system health check...")
        
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_resources": self.check_system_resources(),
            "docker_services": self.check_docker_services(),
            "api_health": self.check_api_health(),
            "redis_health": self.check_redis_health(),
            "database_health": self.check_database_health(),
            "celery_health": self.check_celery_health(),
            "performance_metrics": self.get_performance_metrics(),
        }
        
        # Calculate overall status
        statuses = [
            check.get("status", "unknown") 
            for check in health_report.values() 
            if isinstance(check, dict) and "status" in check
        ]
        
        if "error" in statuses:
            overall_status = "error"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        health_report["overall_status"] = overall_status
        
        return health_report
    
    def print_health_report(self, report: Dict[str, Any]):
        """Print formatted health report"""
        status_icons = {
            "healthy": "✅",
            "warning": "⚠️",
            "error": "❌",
            "unknown": "❓"
        }
        
        overall_status = report.get("overall_status", "unknown")
        print(f"\n{status_icons[overall_status]} Overall System Status: {overall_status.upper()}")
        print(f"📅 Report Time: {report['timestamp']}")
        print("=" * 60)
        
        # System Resources
        resources = report.get("system_resources", {})
        status = resources.get("status", "unknown")
        print(f"\n{status_icons[status]} System Resources:")
        if "error" not in resources:
            print(f"   CPU Usage: {resources.get('cpu_usage', 0):.1f}%")
            print(f"   Memory Usage: {resources.get('memory_usage', 0):.1f}%")
            print(f"   Memory Available: {resources.get('memory_available_gb', 0):.1f} GB")
            print(f"   Disk Usage: {resources.get('disk_usage', 0):.1f}%")
            print(f"   Disk Free: {resources.get('disk_free_gb', 0):.1f} GB")
        else:
            print(f"   Error: {resources.get('error', 'Unknown error')}")
        
        # Docker Services
        docker = report.get("docker_services", {})
        status = docker.get("status", "unknown")
        print(f"\n{status_icons[status]} Docker Services:")
        if "error" not in docker:
            services = docker.get("services", [])
            for service in services:
                service_icon = "✅" if service["healthy"] else "❌"
                print(f"   {service_icon} {service['name']}: {service['state']}")
        else:
            print(f"   Error: {docker.get('error', 'Unknown error')}")
        
        # API Health
        api = report.get("api_health", {})
        status = api.get("status", "unknown")
        print(f"\n{status_icons[status]} API Health:")
        if "error" not in api:
            print(f"   Health Endpoint: {'✅' if api.get('health_endpoint') else '❌'}")
            print(f"   WebSocket Endpoint: {'✅' if api.get('websocket_endpoint') else '❌'}")
            print(f"   Response Time: {api.get('response_time_ms', 0):.1f} ms")
        else:
            print(f"   Error: {api.get('error', 'Unknown error')}")
        
        # Redis Health
        redis_health = report.get("redis_health", {})
        status = redis_health.get("status", "unknown")
        print(f"\n{status_icons[status]} Redis Health:")
        if "error" not in redis_health:
            print(f"   Connection: {'✅' if redis_health.get('ping') else '❌'}")
            print(f"   Memory Usage: {redis_health.get('memory_usage_mb', 0):.1f} MB")
            print(f"   Connected Clients: {redis_health.get('connected_clients', 0)}")
            print(f"   Uptime: {redis_health.get('uptime_seconds', 0)} seconds")
        else:
            print(f"   Error: {redis_health.get('error', 'Unknown error')}")
        
        # Database Health
        db_health = report.get("database_health", {})
        status = db_health.get("status", "unknown")
        print(f"\n{status_icons[status]} Database Health:")
        if "error" not in db_health:
            print(f"   Clients: {db_health.get('clients', 0)}")
            print(f"   Total Posts: {db_health.get('total_posts', 0)}")
            print(f"   Total Responses: {db_health.get('total_responses', 0)}")
            print(f"   Recent Posts (24h): {db_health.get('recent_posts_24h', 0)}")
            print(f"   Recent Responses (24h): {db_health.get('recent_responses_24h', 0)}")
        else:
            print(f"   Error: {db_health.get('error', 'Unknown error')}")
        
        # Celery Health
        celery_health = report.get("celery_health", {})
        status = celery_health.get("status", "unknown")
        print(f"\n{status_icons[status]} Celery Health:")
        if "error" not in celery_health:
            print(f"   Active Workers: {celery_health.get('active_workers', 0)}")
            print(f"   Recent Scan Tasks: {celery_health.get('recent_scan_tasks', 0)}")
        else:
            print(f"   Error: {celery_health.get('error', 'Unknown error')}")
        
        # Performance Metrics
        perf = report.get("performance_metrics", {})
        status = perf.get("status", "unknown")
        print(f"\n{status_icons[status]} Performance Metrics (24h):")
        if "error" not in perf:
            events = perf.get("events_24h", {})
            print(f"   Average Response Quality: {perf.get('avg_response_quality', 0)}")
            print(f"   Events: {sum(events.values())} total")
            for event_type, count in events.items():
                print(f"     - {event_type}: {count}")
            
            top_keywords = perf.get("top_keywords", [])
            if top_keywords:
                print("   Top Keywords:")
                for kw_data in top_keywords[:3]:
                    print(f"     - {kw_data['keyword']}: {kw_data['matches']} matches")
        else:
            print(f"   Error: {perf.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        
        # Recommendations
        if overall_status != "healthy":
            print("\n🔧 Recommendations:")
            
            if resources.get("cpu_usage", 0) > 80:
                print("   - High CPU usage detected. Consider scaling or optimizing tasks.")
            
            if resources.get("memory_usage", 0) > 80:
                print("   - High memory usage detected. Consider increasing RAM or optimizing queries.")
            
            if docker.get("healthy_services", 0) < docker.get("total_services", 1):
                print("   - Some Docker services are not running. Check with: docker-compose ps")
            
            if not api.get("health_endpoint"):
                print("   - API health endpoint not responding. Check backend service.")
            
            if celery_health.get("active_workers", 0) == 0:
                print("   - No Celery workers active. Background tasks won't process.")
            
            print("   - Check logs with: docker-compose logs [service_name]")
            print("   - Restart services with: docker-compose restart")


def main():
    parser = argparse.ArgumentParser(description="Enhanced Reddit Bot System Monitor")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--watch", type=int, help="Watch mode - refresh every N seconds")
    parser.add_argument("--save", type=str, help="Save report to file")
    
    args = parser.parse_args()
    
    monitor = SystemMonitor()
    
    def run_check():
        report = monitor.run_full_health_check()
        
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            monitor.print_health_report(report)
        
        if args.save:
            with open(args.save, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Report saved to: {args.save}")
        
        return report
    
    if args.watch:
        print(f"👀 Watching system health (refreshing every {args.watch} seconds)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                if not args.json:
                    os.system('clear' if os.name == 'posix' else 'cls')
                
                report = run_check()
                
                if not args.json:
                    print(f"\n⏰ Next refresh in {args.watch} seconds...")
                
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
    else:
        run_check()


if __name__ == "__main__":
    main()