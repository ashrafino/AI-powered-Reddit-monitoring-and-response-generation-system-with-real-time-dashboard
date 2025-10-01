#!/usr/bin/env python3
"""
Service Validation Script

This script validates that all required services are running correctly
and communicating properly as part of the core infrastructure validation.
"""

import subprocess
import json
import time
import requests
import redis
import psutil
import logging
from typing import Dict, List, Any, Optional
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.core.config import settings
    from app.db.session import SessionLocal
    from sqlalchemy import text
except ImportError as e:
    print(f"Warning: Could not import app modules: {e}")
    settings = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceValidator:
    def __init__(self):
        self.services_status = {}
        
    def check_docker_services(self) -> Dict[str, Any]:
        """Check Docker Compose services status"""
        logger.info("Checking Docker services...")
        
        try:
            # Check if docker-compose is available
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "error": "Docker Compose not available",
                    "services": []
                }
            
            # Get service status
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "error": f"Failed to get service status: {result.stderr}",
                    "services": []
                }
            
            services = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        service = json.loads(line)
                        services.append({
                            "name": service.get("Service", "unknown"),
                            "state": service.get("State", "unknown"),
                            "status": service.get("Status", "unknown"),
                            "ports": service.get("Ports", ""),
                            "healthy": service.get("State") == "running"
                        })
                    except json.JSONDecodeError:
                        continue
            
            healthy_count = sum(1 for s in services if s["healthy"])
            total_count = len(services)
            
            return {
                "status": "healthy" if healthy_count == total_count and total_count > 0 else "error",
                "services": services,
                "healthy_services": healthy_count,
                "total_services": total_count,
                "all_running": healthy_count == total_count and total_count > 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Docker command timed out",
                "services": []
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "services": []
            }
    
    def check_database_connection(self) -> Dict[str, Any]:
        """Check database connectivity and basic operations"""
        logger.info("Checking database connection...")
        
        if not settings:
            return {
                "status": "error",
                "error": "Settings not available"
            }
        
        try:
            db = SessionLocal()
            
            # Test basic connectivity
            start_time = time.time()
            db.execute(text("SELECT 1"))
            connection_time = (time.time() - start_time) * 1000
            
            # Test table existence
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            result = db.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'clients', 'users', 'client_configs', 'matched_posts', 
                'ai_responses', 'analytics_events', 'performance_metrics', 
                'trend_analysis'
            ]
            
            missing_tables = set(expected_tables) - set(tables)
            
            db.close()
            
            return {
                "status": "healthy" if not missing_tables else "warning",
                "connection_time_ms": connection_time,
                "tables_found": len(tables),
                "expected_tables": len(expected_tables),
                "missing_tables": list(missing_tables),
                "all_tables_exist": not missing_tables
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_redis_connection(self) -> Dict[str, Any]:
        """Check Redis connectivity and basic operations"""
        logger.info("Checking Redis connection...")
        
        if not settings:
            return {
                "status": "error",
                "error": "Settings not available"
            }
        
        try:
            redis_client = redis.from_url(settings.redis_url)
            
            # Test basic connectivity
            start_time = time.time()
            ping_result = redis_client.ping()
            connection_time = (time.time() - start_time) * 1000
            
            # Test basic operations
            test_key = "health_check_test"
            redis_client.set(test_key, "test_value", ex=60)
            test_value = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            # Get Redis info
            info = redis_client.info()
            
            return {
                "status": "healthy",
                "ping": ping_result,
                "connection_time_ms": connection_time,
                "read_write_test": test_value.decode() == "test_value" if test_value else False,
                "memory_usage_mb": info.get('used_memory', 0) / (1024**2),
                "connected_clients": info.get('connected_clients', 0),
                "uptime_seconds": info.get('uptime_in_seconds', 0)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_api_endpoints(self) -> Dict[str, Any]:
        """Check API endpoints availability"""
        logger.info("Checking API endpoints...")
        
        api_base = "http://localhost/api"
        endpoints_to_check = [
            "/health",
            "/health/ready", 
            "/health/live",
            "/health/detailed",
            "/health/metrics"
        ]
        
        results = {}
        overall_healthy = True
        
        for endpoint in endpoints_to_check:
            try:
                start_time = time.time()
                response = requests.get(f"{api_base}{endpoint}", timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                results[endpoint] = {
                    "status": "healthy" if response.status_code == 200 else "error",
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "accessible": response.status_code == 200
                }
                
                if response.status_code != 200:
                    overall_healthy = False
                    
            except Exception as e:
                results[endpoint] = {
                    "status": "error",
                    "error": str(e),
                    "accessible": False
                }
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "error",
            "endpoints": results,
            "all_accessible": overall_healthy
        }
    
    def check_celery_services(self) -> Dict[str, Any]:
        """Check Celery worker and beat scheduler"""
        logger.info("Checking Celery services...")
        
        if not settings:
            return {
                "status": "error",
                "error": "Settings not available"
            }
        
        try:
            from celery import Celery
            
            celery_app = Celery(
                "redditbot",
                broker=settings.celery_broker_url,
                backend=settings.celery_result_backend,
            )
            
            # Check active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            stats = inspect.stats()
            
            worker_count = len(active_workers) if active_workers else 0
            
            # Check if beat scheduler is running (look for scheduled tasks)
            scheduled = inspect.scheduled()
            beat_running = scheduled is not None and len(scheduled) >= 0
            
            return {
                "status": "healthy" if worker_count > 0 else "warning",
                "active_workers": worker_count,
                "worker_details": active_workers or {},
                "worker_stats": stats or {},
                "beat_scheduler_running": beat_running,
                "workers_healthy": worker_count > 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_system_dependencies(self) -> Dict[str, Any]:
        """Check system-level dependencies"""
        logger.info("Checking system dependencies...")
        
        dependencies = {}
        
        # Check Python packages
        required_packages = [
            'fastapi', 'sqlalchemy', 'redis', 'celery', 
            'praw', 'openai', 'psutil', 'requests'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                dependencies[f"python_{package}"] = {
                    "status": "available",
                    "installed": True
                }
            except ImportError:
                dependencies[f"python_{package}"] = {
                    "status": "missing",
                    "installed": False
                }
        
        # Check system resources
        try:
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            dependencies["system_resources"] = {
                "status": "healthy",
                "cpu_cores": cpu_count,
                "total_memory_gb": memory.total / (1024**3),
                "available_memory_gb": memory.available / (1024**3),
                "total_disk_gb": disk.total / (1024**3),
                "free_disk_gb": disk.free / (1024**3),
                "adequate_resources": (
                    memory.available > 1024**3 and  # At least 1GB RAM
                    disk.free > 5 * 1024**3  # At least 5GB disk
                )
            }
        except Exception as e:
            dependencies["system_resources"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Overall status
        missing_packages = [
            k for k, v in dependencies.items() 
            if k.startswith("python_") and not v.get("installed", False)
        ]
        
        overall_status = "healthy"
        if missing_packages:
            overall_status = "error"
        elif not dependencies.get("system_resources", {}).get("adequate_resources", True):
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "dependencies": dependencies,
            "missing_packages": missing_packages
        }
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete service validation"""
        logger.info("Starting comprehensive service validation...")
        
        validation_report = {
            "timestamp": time.time(),
            "docker_services": self.check_docker_services(),
            "database": self.check_database_connection(),
            "redis": self.check_redis_connection(),
            "api_endpoints": self.check_api_endpoints(),
            "celery_services": self.check_celery_services(),
            "system_dependencies": self.check_system_dependencies()
        }
        
        # Calculate overall status
        component_statuses = [
            validation_report[component].get("status", "unknown")
            for component in validation_report
            if isinstance(validation_report[component], dict) and "status" in validation_report[component]
        ]
        
        if "error" in component_statuses:
            overall_status = "error"
        elif "warning" in component_statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        validation_report["overall_status"] = overall_status
        
        # Summary
        validation_report["summary"] = {
            "total_components": len(component_statuses),
            "healthy_components": component_statuses.count("healthy"),
            "warning_components": component_statuses.count("warning"),
            "error_components": component_statuses.count("error"),
            "all_services_operational": overall_status == "healthy"
        }
        
        return validation_report
    
    def print_validation_report(self, report: Dict[str, Any]):
        """Print formatted validation report"""
        status_icons = {
            "healthy": "✅",
            "warning": "⚠️",
            "error": "❌",
            "unknown": "❓"
        }
        
        overall_status = report.get("overall_status", "unknown")
        print(f"\n{status_icons[overall_status]} Overall Service Status: {overall_status.upper()}")
        print(f"📅 Validation Time: {time.ctime(report['timestamp'])}")
        
        summary = report.get("summary", {})
        print(f"🔍 Components: {summary.get('healthy_components', 0)}/{summary.get('total_components', 0)} healthy")
        print("=" * 60)
        
        # Docker Services
        docker = report.get("docker_services", {})
        status = docker.get("status", "unknown")
        print(f"\n{status_icons[status]} Docker Services:")
        if docker.get("services"):
            for service in docker["services"]:
                service_icon = "✅" if service["healthy"] else "❌"
                print(f"   {service_icon} {service['name']}: {service['state']} ({service['status']})")
        else:
            print(f"   Error: {docker.get('error', 'No services found')}")
        
        # Database
        db = report.get("database", {})
        status = db.get("status", "unknown")
        print(f"\n{status_icons[status]} Database:")
        if "error" not in db:
            print(f"   Connection Time: {db.get('connection_time_ms', 0):.1f}ms")
            print(f"   Tables: {db.get('tables_found', 0)}/{db.get('expected_tables', 0)}")
            if db.get("missing_tables"):
                print(f"   Missing Tables: {', '.join(db['missing_tables'])}")
        else:
            print(f"   Error: {db.get('error', 'Unknown error')}")
        
        # Redis
        redis_status = report.get("redis", {})
        status = redis_status.get("status", "unknown")
        print(f"\n{status_icons[status]} Redis:")
        if "error" not in redis_status:
            print(f"   Connection Time: {redis_status.get('connection_time_ms', 0):.1f}ms")
            print(f"   Read/Write Test: {'✅' if redis_status.get('read_write_test') else '❌'}")
            print(f"   Memory Usage: {redis_status.get('memory_usage_mb', 0):.1f}MB")
            print(f"   Connected Clients: {redis_status.get('connected_clients', 0)}")
        else:
            print(f"   Error: {redis_status.get('error', 'Unknown error')}")
        
        # API Endpoints
        api = report.get("api_endpoints", {})
        status = api.get("status", "unknown")
        print(f"\n{status_icons[status]} API Endpoints:")
        if api.get("endpoints"):
            for endpoint, endpoint_data in api["endpoints"].items():
                endpoint_icon = "✅" if endpoint_data.get("accessible") else "❌"
                response_time = endpoint_data.get("response_time_ms", 0)
                print(f"   {endpoint_icon} {endpoint}: {response_time:.1f}ms")
        else:
            print("   No endpoints checked")
        
        # Celery Services
        celery = report.get("celery_services", {})
        status = celery.get("status", "unknown")
        print(f"\n{status_icons[status]} Celery Services:")
        if "error" not in celery:
            print(f"   Active Workers: {celery.get('active_workers', 0)}")
            print(f"   Beat Scheduler: {'✅' if celery.get('beat_scheduler_running') else '❌'}")
        else:
            print(f"   Error: {celery.get('error', 'Unknown error')}")
        
        # System Dependencies
        deps = report.get("system_dependencies", {})
        status = deps.get("status", "unknown")
        print(f"\n{status_icons[status]} System Dependencies:")
        if deps.get("missing_packages"):
            print(f"   Missing Packages: {', '.join(deps['missing_packages'])}")
        else:
            print("   All required packages installed")
        
        sys_resources = deps.get("dependencies", {}).get("system_resources", {})
        if sys_resources and "error" not in sys_resources:
            print(f"   CPU Cores: {sys_resources.get('cpu_cores', 0)}")
            print(f"   Available Memory: {sys_resources.get('available_memory_gb', 0):.1f}GB")
            print(f"   Free Disk Space: {sys_resources.get('free_disk_gb', 0):.1f}GB")
        
        print("\n" + "=" * 60)
        
        # Recommendations
        if overall_status != "healthy":
            print("\n🔧 Recommendations:")
            
            if docker.get("status") == "error":
                print("   - Start Docker services: docker-compose up -d")
            
            if db.get("status") == "error":
                print("   - Check database connection and credentials")
                print("   - Ensure PostgreSQL is running")
            
            if redis_status.get("status") == "error":
                print("   - Check Redis connection")
                print("   - Ensure Redis server is running")
            
            if api.get("status") == "error":
                print("   - Start the API server")
                print("   - Check API logs for errors")
            
            if celery.get("active_workers", 0) == 0:
                print("   - Start Celery workers: celery -A app.celery_app worker --loglevel=info")
            
            if deps.get("missing_packages"):
                print("   - Install missing packages: pip install -r requirements.txt")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Service Validation Tool")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--save", type=str, help="Save report to file")
    
    args = parser.parse_args()
    
    validator = ServiceValidator()
    report = validator.run_full_validation()
    
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        validator.print_validation_report(report)
    
    if args.save:
        with open(args.save, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 Report saved to: {args.save}")
    
    # Exit with error code if services are not healthy
    if report.get("overall_status") != "healthy":
        sys.exit(1)


if __name__ == "__main__":
    main()