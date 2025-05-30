"""
Azure-integrated version of the TerraFusion API Gateway.

This is a modified version of app.py configured to run in Azure App Service with
Application Insights monitoring integrated.
"""

import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Import Application Insights integration
from app_insights_integration import setup_app_insights_for_flask, track_custom_event, track_exception

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure Flask app
app.secret_key = os.environ.get("SESSION_SECRET", "TerraFusionDevSecret")  # Default for development only
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # For correct URL generation behind proxies

# Configure the database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Set up Azure Application Insights
app_insights_middleware = setup_app_insights_for_flask(app)

# Import routes and models after the app is created
with app.app_context():
    # Import models
    import models  # noqa: F401
    
    # Create database tables if they don't exist
    db.create_all()
    
    # Import routes from app.py
    from app import (
        login_page, root, dashboard, sync_dashboard, 
        sync_pairs, create_sync_pair, view_sync_pair,
        edit_sync_pair, toggle_sync_pair_status, run_sync_operation,
        new_sync_wizard, metrics_dashboard, market_analysis_dashboard,
        gis_export_dashboard, audit_dashboard, architecture_visualization,
        view_logs, api_docs, status, trigger_health_check, health_check,
        liveness_check, readiness_check, get_sync_pairs, get_sync_pair, 
        get_sync_operations, get_system_metrics, refresh_metrics, 
        get_architecture_data, get_metrics_status, get_audit_entries,
        get_audit_entry, get_audit_summary, proxy, create_audit_log
    )
    
    # Register the functions with the app (routes will be imported from original app.py)
    
    # Add middleware for Azure logging
    @app.before_request
    def before_request_middleware():
        """Middleware to run before each request."""
        track_custom_event("api_request", {
            "path": request.path,
            "method": request.method,
            "endpoint": request.endpoint
        })
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global exception handler for error tracking."""
        track_exception(e)
        # Continue with normal exception handling
        return "An error occurred", 500

# Application health check for Azure
@app.route("/azure-health")
def azure_health_check():
    """Special health check for Azure App Service."""
    try:
        # Check database connection
        with db.engine.connect() as connection:
            connection.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "TerraFusion API Gateway",
            "database": "connected",
            "version": "Azure Edition 1.0"
        }, 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "TerraFusion API Gateway",
            "error": str(e)
        }, 500

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting TerraFusion Azure-integrated API Gateway on port {port}")
    app.run(host="0.0.0.0", port=port)