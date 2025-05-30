#!/usr/bin/env python3
"""
Simple test for the GIS Export plugin health check endpoint.
"""

import requests
import sys

def test_gis_export_plugin_health(host="localhost"):
    """Test the GIS Export plugin health check endpoint."""
    base_url = f"http://{host}:8080/plugins/v1/gis-export"
    
    # Health check
    response = requests.get(f"{base_url}/health")
    print(f"Health check status code: {response.status_code}")
    print(f"Health check response: {response.text}")
    assert response.status_code == 200
    
    health_data = response.json()
    assert health_data["status"] == "healthy"
    assert health_data["plugin"] == "gis_export"
    print(f"✅ Health check passed. Plugin version: {health_data['version']}")

if __name__ == "__main__":
    host = "localhost"
    if len(sys.argv) > 1:
        host = sys.argv[1]
    
    test_gis_export_plugin_health(host)