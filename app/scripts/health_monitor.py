#!/usr/bin/env python3
"""
Automated Health Monitoring Script

This script provides automated health monitoring with alerting capabilities
for the Reddit Bot System. It can be run as a cron job or standalone monitor.
"""

import asyncio
import json
import time
import requests
import smtplib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.core.config import settings
except ImportError:
    print("Warning: Could not import app settings. Using default configuration.")
    settings = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self, api_base: str = "http://localhost/api"):
        self.api_base = api_base
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 80.0,
            "disk_usage": 90.0,
            "response_time_ms": 5000.0,
            "redis_memory_percent": 80.0
        }
        self.alert_history = []
        
    def check_api_health(self) -> Dict[str, Any]:
        """Check API health endpoints"""
        try:
            start_time = time.time()
            
            # Basic health check
            health_response = requests.get(f"{self.api_base}/health", timeout=10)
            health_time = (time.time() - start_time) * 1000
            
            # Detailed health check
            detailed_response = requests.get(f"{self.api_base}/health/detailed", timeout=30)
            detailed_data = detailed_response.json() if detailed_response.status_code == 200 else {}
            
            # Metrics check
            metrics_response = requests.get(f"{self.api_base}/health/metrics", timeout=30)
            metrics_data = metrics_response.json() if metrics_response.status_code == 200 else {}
            
            # Dependencies check
            deps_response = requests.get(f"{self.api_base}/health/dependencies", timeout=10)
            deps_data = deps_response.json() if deps_response.status_code == 200 else {}
            
            # Celery check
            celery_response = requests.get(f"{self.api_base}/health/celery", timeout=10)
            celery_data = celery_response.json() if celery_response.status_code == 200 else {}
            
            return {
                "status": "healthy" if health_response.status_code == 200 else "error",
                "response_time_ms": health_time,
                "endpoints": {
                    "health": health_response.status_code == 200,
                    "detailed": detailed_response.status_code == 200,
                    "metrics": metrics_response.status_code == 200,
                    "dependencies": deps_response.status_code == 200,
                    "celery": celery_response.status_code == 200
                },
                "detailed_health": detailed_data,
                "metrics": metrics_data,
                "dependencies": deps_data,
                "celery": celery_data
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "endpoints": {
                    "health": False,
                    "detailed": False,
                    "metrics": False,
                    "dependencies": False,
                    "celery": False
                }
            }
    
    def analyze_health_data(self, health_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze health data and identify issues"""
        issues = []
        
        # Check API availability
        if health_data.get("status") == "error":
            issues.append({
                "severity": "critical",
                "component": "api",
                "message": f"API is not responding: {health_data.get('error', 'Unknown error')}",
                "timestamp": datetime.utcnow().isoformat()
            })
            return issues  # If API is down, can't check other components
        
        # Check response time
        response_time = health_data.get("response_time_ms", 0)
        if response_time > self.alert_thresholds["response_time_ms"]:
            issues.append({
                "severity": "warning",
                "component": "api",
                "message": f"High API response time: {response_time:.1f}ms (threshold: {self.alert_thresholds['response_time_ms']}ms)",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        detailed_health = health_data.get("detailed_health", {})
        
        # Check database
        db_health = detailed_health.get("database", {})
        if db_health.get("status") == "error":
            issues.append({
                "severity": "critical",
                "component": "database",
                "message": f"Database connection failed: {db_health.get('error', 'Unknown error')}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check Redis
        redis_health = detailed_health.get("redis", {})
        if redis_health.get("status") == "error":
            issues.append({
                "severity": "critical",
                "component": "redis",
                "message": f"Redis connection failed: {redis_health.get('error', 'Unknown error')}",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif redis_health.get("memory_percent", 0) > self.alert_thresholds["redis_memory_percent"]:
            issues.append({
                "severity": "warning",
                "component": "redis",
                "message": f"High Redis memory usage: {redis_health.get('memory_percent', 0):.1f}% (threshold: {self.alert_thresholds['redis_memory_percent']}%)",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check system resources
        system_health = detailed_health.get("system", {})
        if system_health.get("status") == "error":
            issues.append({
                "severity": "warning",
                "component": "system",
                "message": f"System monitoring failed: {system_health.get('error', 'Unknown error')}",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            cpu_usage = system_health.get("cpu_usage", 0)
            memory_usage = system_health.get("memory_usage", 0)
            disk_usage = system_health.get("disk_usage", 0)
            
            if cpu_usage > self.alert_thresholds["cpu_usage"]:
                issues.append({
                    "severity": "warning",
                    "component": "system",
                    "message": f"High CPU usage: {cpu_usage:.1f}% (threshold: {self.alert_thresholds['cpu_usage']}%)",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            if memory_usage > self.alert_thresholds["memory_usage"]:
                issues.append({
                    "severity": "warning",
                    "component": "system",
                    "message": f"High memory usage: {memory_usage:.1f}% (threshold: {self.alert_thresholds['memory_usage']}%)",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            if disk_usage > self.alert_thresholds["disk_usage"]:
                issues.append({
                    "severity": "critical",
                    "component": "system",
                    "message": f"High disk usage: {disk_usage:.1f}% (threshold: {self.alert_thresholds['disk_usage']}%)",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check Celery workers
        celery_data = health_data.get("celery", {})
        if celery_data.get("status") == "error":
            issues.append({
                "severity": "critical",
                "component": "celery",
                "message": f"Celery workers not responding: {celery_data.get('error', 'Unknown error')}",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif celery_data.get("active_workers", 0) == 0:
            issues.append({
                "severity": "critical",
                "component": "celery",
                "message": "No active Celery workers found. Background tasks will not process.",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check dependencies
        dependencies = health_data.get("dependencies", {}).get("dependencies", {})
        critical_deps = ["openai", "reddit"]
        
        for dep_name in critical_deps:
            dep_info = dependencies.get(dep_name, {})
            if dep_info.get("status") == "not_configured":
                issues.append({
                    "severity": "warning",
                    "component": "dependencies",
                    "message": f"{dep_name.title()} API not configured. Some features may not work.",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif dep_info.get("status") == "error":
                issues.append({
                    "severity": "warning",
                    "component": "dependencies",
                    "message": f"{dep_name.title()} API error: {dep_info.get('error', 'Unknown error')}",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return issues
    
    def send_alert_email(self, issues: List[Dict[str, Any]], health_data: Dict[str, Any]):
        """Send alert email for critical issues"""
        if not settings or not settings.smtp_host or not settings.smtp_user:
            logger.warning("Email configuration not available. Cannot send alerts.")
            return
        
        critical_issues = [issue for issue in issues if issue["severity"] == "critical"]
        if not critical_issues:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.email_from or settings.smtp_user
            msg['To'] = settings.smtp_user  # Send to admin
            msg['Subject'] = f"🚨 Reddit Bot System Alert - {len(critical_issues)} Critical Issues"
            
            # Create email body
            body = f"""
Reddit Bot System Health Alert

Time: {datetime.utcnow().isoformat()}
Critical Issues Found: {len(critical_issues)}
Total Issues: {len(issues)}

CRITICAL ISSUES:
"""
            
            for issue in critical_issues:
                body += f"""
- Component: {issue['component'].upper()}
  Message: {issue['message']}
  Time: {issue['timestamp']}
"""
            
            if len(issues) > len(critical_issues):
                body += f"\n\nADDITIONAL WARNINGS: {len(issues) - len(critical_issues)}\n"
                warning_issues = [issue for issue in issues if issue["severity"] == "warning"]
                for issue in warning_issues:
                    body += f"- {issue['component']}: {issue['message']}\n"
            
            # Add system summary
            detailed_health = health_data.get("detailed_health", {})
            if detailed_health:
                body += f"""

SYSTEM SUMMARY:
- Overall Status: {detailed_health.get('overall_status', 'unknown').upper()}
- API Response Time: {health_data.get('response_time_ms', 0):.1f}ms
"""
                
                system_info = detailed_health.get("system", {})
                if system_info and "error" not in system_info:
                    body += f"""- CPU Usage: {system_info.get('cpu_usage', 0):.1f}%
- Memory Usage: {system_info.get('memory_usage', 0):.1f}%
- Disk Usage: {system_info.get('disk_usage', 0):.1f}%
"""
            
            body += f"""

Please check the system immediately and take corrective action.

Dashboard: http://localhost:3000
API Health: {self.api_base}/health/detailed

This is an automated alert from the Reddit Bot System Health Monitor.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            text = msg.as_string()
            server.sendmail(settings.smtp_user, settings.smtp_user, text)
            server.quit()
            
            logger.info(f"Alert email sent for {len(critical_issues)} critical issues")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
    
    def should_send_alert(self, issues: List[Dict[str, Any]]) -> bool:
        """Determine if an alert should be sent (avoid spam)"""
        critical_issues = [issue for issue in issues if issue["severity"] == "critical"]
        if not critical_issues:
            return False
        
        # Check if we've sent an alert for similar issues recently (within 1 hour)
        now = datetime.utcnow()
        recent_alerts = [
            alert for alert in self.alert_history 
            if now - datetime.fromisoformat(alert["timestamp"]) < timedelta(hours=1)
        ]
        
        # If we have recent alerts for the same components, don't spam
        recent_components = set()
        for alert in recent_alerts:
            recent_components.update(alert["components"])
        
        current_components = set(issue["component"] for issue in critical_issues)
        
        # Send alert if there are new critical components or if it's been more than 1 hour
        if not recent_components or not current_components.issubset(recent_components):
            return True
        
        return False
    
    def record_alert(self, issues: List[Dict[str, Any]]):
        """Record that an alert was sent"""
        critical_issues = [issue for issue in issues if issue["severity"] == "critical"]
        if critical_issues:
            self.alert_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "components": [issue["component"] for issue in critical_issues],
                "issue_count": len(critical_issues)
            })
            
            # Keep only last 24 hours of alert history
            cutoff = datetime.utcnow() - timedelta(hours=24)
            self.alert_history = [
                alert for alert in self.alert_history
                if datetime.fromisoformat(alert["timestamp"]) > cutoff
            ]
    
    def run_health_check(self, send_alerts: bool = True) -> Dict[str, Any]:
        """Run comprehensive health check"""
        logger.info("Starting health check...")
        
        # Get health data
        health_data = self.check_api_health()
        
        # Analyze for issues
        issues = self.analyze_health_data(health_data)
        
        # Create report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy" if not issues else ("critical" if any(i["severity"] == "critical" for i in issues) else "warning"),
            "issues_found": len(issues),
            "critical_issues": len([i for i in issues if i["severity"] == "critical"]),
            "warning_issues": len([i for i in issues if i["severity"] == "warning"]),
            "issues": issues,
            "health_data": health_data
        }
        
        # Send alerts if needed
        if send_alerts and issues and self.should_send_alert(issues):
            self.send_alert_email(issues, health_data)
            self.record_alert(issues)
        
        # Log results
        if issues:
            critical_count = len([i for i in issues if i["severity"] == "critical"])
            warning_count = len([i for i in issues if i["severity"] == "warning"])
            logger.warning(f"Health check completed: {critical_count} critical, {warning_count} warning issues found")
            
            for issue in issues:
                level = logging.ERROR if issue["severity"] == "critical" else logging.WARNING
                logger.log(level, f"{issue['component'].upper()}: {issue['message']}")
        else:
            logger.info("Health check completed: All systems healthy")
        
        return report
    
    def print_health_report(self, report: Dict[str, Any]):
        """Print formatted health report"""
        status_icons = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌",
            "error": "💥"
        }
        
        overall_status = report.get("overall_status", "unknown")
        print(f"\n{status_icons.get(overall_status, '❓')} Overall System Status: {overall_status.upper()}")
        print(f"📅 Report Time: {report['timestamp']}")
        print(f"🔍 Issues Found: {report['issues_found']} ({report['critical_issues']} critical, {report['warning_issues']} warnings)")
        print("=" * 60)
        
        if report["issues"]:
            print("\n🚨 ISSUES DETECTED:")
            for issue in report["issues"]:
                icon = "💥" if issue["severity"] == "critical" else "⚠️"
                print(f"{icon} [{issue['component'].upper()}] {issue['message']}")
        
        # Show key metrics
        health_data = report.get("health_data", {})
        detailed_health = health_data.get("detailed_health", {})
        
        if detailed_health:
            print(f"\n📊 KEY METRICS:")
            print(f"   API Response Time: {health_data.get('response_time_ms', 0):.1f}ms")
            
            system_info = detailed_health.get("system", {})
            if system_info and "error" not in system_info:
                print(f"   CPU Usage: {system_info.get('cpu_usage', 0):.1f}%")
                print(f"   Memory Usage: {system_info.get('memory_usage', 0):.1f}%")
                print(f"   Disk Usage: {system_info.get('disk_usage', 0):.1f}%")
            
            redis_info = detailed_health.get("redis", {})
            if redis_info and "error" not in redis_info:
                print(f"   Redis Memory: {redis_info.get('memory_usage_mb', 0):.1f}MB")
                print(f"   Redis Clients: {redis_info.get('connected_clients', 0)}")
            
            celery_info = health_data.get("celery", {})
            if celery_info and "error" not in celery_info:
                print(f"   Celery Workers: {celery_info.get('active_workers', 0)}")
        
        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Reddit Bot System Health Monitor")
    parser.add_argument("--api-base", default="http://localhost/api", help="API base URL")
    parser.add_argument("--no-alerts", action="store_true", help="Disable email alerts")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--watch", type=int, help="Watch mode - check every N seconds")
    parser.add_argument("--save", type=str, help="Save report to file")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode - only log errors")
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    monitor = HealthMonitor(api_base=args.api_base)
    
    def run_check():
        report = monitor.run_health_check(send_alerts=not args.no_alerts)
        
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            monitor.print_health_report(report)
        
        if args.save:
            with open(args.save, 'w') as f:
                json.dump(report, f, indent=2)
            if not args.quiet:
                print(f"\n📄 Report saved to: {args.save}")
        
        return report
    
    if args.watch:
        if not args.quiet:
            print(f"👀 Monitoring system health (checking every {args.watch} seconds)")
            print("Press Ctrl+C to stop")
        
        try:
            while True:
                if not args.json and not args.quiet:
                    os.system('clear' if os.name == 'posix' else 'cls')
                
                report = run_check()
                
                if not args.json and not args.quiet:
                    print(f"\n⏰ Next check in {args.watch} seconds...")
                
                time.sleep(args.watch)
        except KeyboardInterrupt:
            if not args.quiet:
                print("\n👋 Monitoring stopped")
    else:
        report = run_check()
        
        # Exit with error code if critical issues found
        if report.get("critical_issues", 0) > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()