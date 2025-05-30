"""
TerraFusion Platform - Improved Routes

These routes implement the improved UI/UX based on the Senior Engineer's action plan.
They serve the updated templates with better user flow and data state communication.
"""

from flask import Blueprint, render_template, redirect, url_for

# Create Blueprint
improved_bp = Blueprint('improved', __name__, url_prefix='/improved')

@improved_bp.route('/')
def index():
    """Improved home page."""
    return render_template('improved/index.html')

@improved_bp.route('/dashboard')
def dashboard():
    """Improved dashboard page."""
    return render_template('improved/dashboard.html')

@improved_bp.route('/gis-export')
def gis_export():
    """Improved GIS Export dashboard."""
    return render_template('gis_export_dashboard_improved.html')

@improved_bp.route('/sync-operations')
def sync_operations():
    """Improved Sync Operations dashboard."""
    return render_template('improved/sync_operations.html')

@improved_bp.route('/metrics')
def metrics():
    """Improved metrics dashboard."""
    return render_template('improved/metrics.html')

@improved_bp.route('/architecture')
def architecture():
    """Improved architecture visualization."""
    return render_template('improved/architecture.html')

@improved_bp.route('/audit')
def audit():
    """Improved audit trail dashboard."""
    return render_template('improved/audit.html')