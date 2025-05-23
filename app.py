"""
TerraFusion Platform - Simplified Application

This module provides a basic Flask application to demonstrate the TerraFusion Platform dashboard.
"""

import os
from flask import Flask, render_template, redirect, url_for

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "terrafusion-dev-key")

# Route definitions
@app.route('/')
def index():
    """Root endpoint redirects to dashboard."""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard view."""
    return render_template('dashboard.html')

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "TerraFusion Platform", "version": "1.0.0"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)