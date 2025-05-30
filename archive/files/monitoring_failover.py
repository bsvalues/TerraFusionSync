
import os
import time
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
import json
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TerraFusionFailoverMonitor:
    """
    Production-grade failover monitoring for 99.9% uptime guarantee.
    Monitors services, logs failures, triggers alerts, and manages backups.
    """
    
    def __init__(self):
        self.services = {
            "api_gateway": {
                "url": "http://0.0.0.0:5000/health",
                "timeout": 10,
                "critical": True
            },
            "sync_service": {
                "url": "http://0.0.0.0:8080/health",
                "timeout": 15,
                "critical": True
            },
            "database": {
                "check_function": self._check_database,
                "timeout": 5,
                "critical": True
            }
        }
        
        self.alert_config = {
            "email_enabled": os.environ.get("ALERT_EMAIL_ENABLED", "false").lower() == "true",
            "smtp_server": os.environ.get("SMTP_SERVER", "localhost"),
            "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
            "smtp_user": os.environ.get("SMTP_USER"),
            "smtp_pass": os.environ.get("SMTP_PASS"),
            "alert_recipients": os.environ.get("ALERT_RECIPIENTS", "").split(","),
            "slack_webhook": os.environ.get("SLACK_WEBHOOK_URL")
        }
        
        self.uptime_log = Path("logs/uptime_monitoring.json")
        self.uptime_log.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize uptime tracking
        self.uptime_stats = self._load_uptime_stats()
        
    def _load_uptime_stats(self) -> Dict:
        """Load existing uptime statistics"""
        if self.uptime_log.exists():
            try:
                with open(self.uptime_log, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "start_time": datetime.now().isoformat(),
            "total_checks": 0,
            "failed_checks": 0,
            "service_failures": {},
            "last_failure": None,
            "uptime_percentage": 100.0,
            "downtime_incidents": []
        }
    
    def _save_uptime_stats(self):
        """Save uptime statistics"""
        with open(self.uptime_log, 'w') as f:
            json.dump(self.uptime_stats, f, indent=2)
    
    def _check_database(self) -> bool:
        """Check database connectivity"""
        try:
            import sqlite3
            # Check if we can connect to database
            conn = sqlite3.connect("terrafusion.db", timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False
    
    def check_service_health(self, service_name: str, config: Dict) -> bool:
        """Check health of individual service"""
        try:
            if "url" in config:
                response = requests.get(config["url"], timeout=config["timeout"])
                return response.status_code == 200
            elif "check_function" in config:
                return config["check_function"]()
            return False
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return False
    
    def send_alert(self, subject: str, message: str, critical: bool = False):
        """Send alert via email and Slack"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] TerraFusion Alert\n\n{message}"
        
        # Log alert
        logger.error(f"ALERT: {subject} - {message}")
        
        # Email alert
        if self.alert_config["email_enabled"] and self.alert_config["smtp_user"]:
            try:
                msg = MimeMultipart()
                msg['From'] = self.alert_config["smtp_user"]
                msg['To'] = ", ".join(self.alert_config["alert_recipients"])
                msg['Subject'] = f"🚨 TerraFusion Alert: {subject}"
                
                msg.attach(MimeText(full_message, 'plain'))
                
                server = smtplib.SMTP(self.alert_config["smtp_server"], self.alert_config["smtp_port"])
                server.starttls()
                server.login(self.alert_config["smtp_user"], self.alert_config["smtp_pass"])
                server.send_message(msg)
                server.quit()
                
                logger.info("Alert email sent successfully")
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
        
        # Slack alert
        if self.alert_config["slack_webhook"]:
            try:
                slack_payload = {
                    "text": f"🚨 TerraFusion Alert: {subject}",
                    "attachments": [{
                        "color": "danger" if critical else "warning",
                        "fields": [{
                            "title": "Alert Details",
                            "value": message,
                            "short": False
                        }],
                        "ts": int(time.time())
                    }]
                }
                
                requests.post(self.alert_config["slack_webhook"], json=slack_payload, timeout=10)
                logger.info("Slack alert sent successfully")
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")
    
    def run_health_checks(self) -> Dict[str, bool]:
        """Run health checks on all services"""
        results = {}
        failure_detected = False
        
        for service_name, config in self.services.items():
            is_healthy = self.check_service_health(service_name, config)
            results[service_name] = is_healthy
            
            if not is_healthy:
                failure_detected = True
                
                # Track service-specific failures
                if service_name not in self.uptime_stats["service_failures"]:
                    self.uptime_stats["service_failures"][service_name] = 0
                self.uptime_stats["service_failures"][service_name] += 1
                
                # Send alert for critical services
                if config.get("critical", False):
                    self.send_alert(
                        f"Service Failure: {service_name}",
                        f"Critical service {service_name} is not responding. Immediate attention required.",
                        critical=True
                    )
        
        # Update uptime statistics
        self.uptime_stats["total_checks"] += 1
        if failure_detected:
            self.uptime_stats["failed_checks"] += 1
            self.uptime_stats["last_failure"] = datetime.now().isoformat()
            
            # Record downtime incident
            incident = {
                "timestamp": datetime.now().isoformat(),
                "failed_services": [name for name, healthy in results.items() if not healthy],
                "duration_estimated": "ongoing"
            }
            self.uptime_stats["downtime_incidents"].append(incident)
        
        # Calculate uptime percentage
        if self.uptime_stats["total_checks"] > 0:
            success_rate = (self.uptime_stats["total_checks"] - self.uptime_stats["failed_checks"]) / self.uptime_stats["total_checks"]
            self.uptime_stats["uptime_percentage"] = success_rate * 100
        
        self._save_uptime_stats()
        
        return results
    
    def automated_backup_on_failure(self):
        """Trigger automated backup when failures detected"""
        try:
            logger.info("Triggering automated backup due to service failure")
            
            # Database backup
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Simple SQLite backup
            import shutil
            backup_file = f"backups/emergency_backup_{backup_timestamp}.db"
            os.makedirs("backups", exist_ok=True)
            
            if os.path.exists("terrafusion.db"):
                shutil.copy2("terrafusion.db", backup_file)
                logger.info(f"Emergency database backup created: {backup_file}")
            
            # Configuration backup
            config_backup = f"backups/config_backup_{backup_timestamp}.tar.gz"
            os.system(f"tar -czf {config_backup} *.py *.json *.env 2>/dev/null || true")
            
            logger.info("Emergency backup completed")
            
        except Exception as e:
            logger.error(f"Emergency backup failed: {e}")
    
    def get_uptime_report(self) -> Dict:
        """Generate comprehensive uptime report"""
        now = datetime.now()
        start_time = datetime.fromisoformat(self.uptime_stats["start_time"])
        total_runtime = (now - start_time).total_seconds()
        
        report = {
            "monitoring_period": {
                "start": self.uptime_stats["start_time"],
                "current": now.isoformat(),
                "total_hours": total_runtime / 3600
            },
            "uptime_metrics": {
                "current_uptime_percentage": self.uptime_stats["uptime_percentage"],
                "target_uptime": 99.9,
                "meets_sla": self.uptime_stats["uptime_percentage"] >= 99.9,
                "total_checks": self.uptime_stats["total_checks"],
                "failed_checks": self.uptime_stats["failed_checks"]
            },
            "failure_analysis": {
                "service_failures": self.uptime_stats["service_failures"],
                "last_failure": self.uptime_stats["last_failure"],
                "recent_incidents": self.uptime_stats["downtime_incidents"][-10:]  # Last 10 incidents
            }
        }
        
        return report
    
    def continuous_monitoring(self, check_interval: int = 60):
        """Run continuous monitoring with specified interval"""
        logger.info(f"Starting continuous monitoring with {check_interval}s intervals")
        
        while True:
            try:
                results = self.run_health_checks()
                
                # Check if any critical services are down
                critical_failures = [
                    name for name, healthy in results.items() 
                    if not healthy and self.services[name].get("critical", False)
                ]
                
                if critical_failures:
                    logger.error(f"Critical service failures detected: {critical_failures}")
                    self.automated_backup_on_failure()
                else:
                    logger.info("All services healthy")
                
                # Generate uptime report every hour
                if self.uptime_stats["total_checks"] % 60 == 0:  # Every 60 checks (1 hour at 60s intervals)
                    report = self.get_uptime_report()
                    logger.info(f"Uptime Report: {report['uptime_metrics']['current_uptime_percentage']:.2f}% (Target: 99.9%)")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(check_interval)

def main():
    """Main monitoring function"""
    monitor = TerraFusionFailoverMonitor()
    
    # Run initial health check
    results = monitor.run_health_checks()
    print("Initial Health Check Results:")
    for service, healthy in results.items():
        status = "✅ HEALTHY" if healthy else "❌ FAILED"
        print(f"  {service}: {status}")
    
    # Generate and display uptime report
    report = monitor.get_uptime_report()
    print(f"\nUptime Status: {report['uptime_metrics']['current_uptime_percentage']:.2f}%")
    print(f"SLA Target: {report['uptime_metrics']['target_uptime']}%")
    print(f"Meets SLA: {'✅ YES' if report['uptime_metrics']['meets_sla'] else '❌ NO'}")
    
    # Start continuous monitoring
    print("\nStarting continuous monitoring...")
    monitor.continuous_monitoring()

if __name__ == "__main__":
    main()
