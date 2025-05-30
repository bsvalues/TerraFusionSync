"""
Azure Application Insights integration for TerraFusion Platform.

This module provides functions to integrate Azure Application Insights
monitoring into both the Flask API Gateway and FastAPI SyncService.
"""

import os
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
import logging

def setup_app_insights_for_flask(app):
    """
    Set up Azure Application Insights for Flask API Gateway.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Flask middleware
    """
    # Get instrumentation key from environment variable
    instrumentation_key = os.environ.get('APPINSIGHTS_INSTRUMENTATIONKEY')
    
    if not instrumentation_key:
        app.logger.warning("Application Insights instrumentation key not found. Monitoring disabled.")
        return None
    
    # Set up Azure logging
    logger = logging.getLogger(__name__)
    handler = AzureLogHandler(connection_string=f'InstrumentationKey={instrumentation_key}')
    logger.addHandler(handler)
    
    # Set up Flask middleware for request tracking
    middleware = FlaskMiddleware(
        app,
        exporter=AzureExporter(connection_string=f'InstrumentationKey={instrumentation_key}'),
        sampler=ProbabilitySampler(rate=1.0),
    )
    
    # Set up metrics collection
    exporter = metrics_exporter.new_metrics_exporter(
        connection_string=f'InstrumentationKey={instrumentation_key}'
    )
    
    app.logger.info("Azure Application Insights integration configured successfully")
    return middleware

def setup_app_insights_for_fastapi(app):
    """
    Set up Azure Application Insights for FastAPI SyncService.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Configured middleware
    """
    from opencensus.ext.fastapi.fastapi_middleware import FastApiMiddleware
    
    # Get instrumentation key from environment variable
    instrumentation_key = os.environ.get('APPINSIGHTS_INSTRUMENTATIONKEY')
    
    if not instrumentation_key:
        logging.warning("Application Insights instrumentation key not found. Monitoring disabled.")
        return None
    
    # Set up Azure logging
    logger = logging.getLogger(__name__)
    handler = AzureLogHandler(connection_string=f'InstrumentationKey={instrumentation_key}')
    logger.addHandler(handler)
    
    # Set up FastAPI middleware
    middleware = FastApiMiddleware(
        app,
        exporter=AzureExporter(connection_string=f'InstrumentationKey={instrumentation_key}'),
        sampler=ProbabilitySampler(rate=1.0),
    )
    
    # Set up metrics collection
    exporter = metrics_exporter.new_metrics_exporter(
        connection_string=f'InstrumentationKey={instrumentation_key}'
    )
    
    logging.info("Azure Application Insights integration configured successfully")
    return middleware

def track_custom_event(name, properties=None):
    """
    Track a custom event in Application Insights.
    
    Args:
        name: Name of the event
        properties: Dictionary of custom properties
    """
    logger = logging.getLogger(__name__)
    properties = properties or {}
    logger.info(f"Custom event: {name}", extra={"custom_dimensions": properties})

def track_dependency(name, dependency_type, target, success=True, duration=0, data=None):
    """
    Track a dependency call in Application Insights (e.g., database or API calls).
    
    Args:
        name: Name of the dependency
        dependency_type: Type of dependency (SQL, HTTP, etc.)
        target: Target of the dependency (server name, URL, etc.)
        success: Whether the dependency call was successful
        duration: Duration of the call in milliseconds
        data: Additional data about the call
    """
    logger = logging.getLogger(__name__)
    properties = {
        "dependency_name": name,
        "dependency_type": dependency_type,
        "dependency_target": target,
        "dependency_success": success,
        "dependency_duration": duration,
        "dependency_data": data or {}
    }
    logger.info(f"Dependency: {name}", extra={"custom_dimensions": properties})

def track_exception(exception):
    """
    Track an exception in Application Insights.
    
    Args:
        exception: Exception object
    """
    logger = logging.getLogger(__name__)
    logger.exception(f"Exception: {str(exception)}")