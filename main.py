"""
Main entry point for the TerraFusion SyncService API Gateway.

Architecture Overview:
---------------------
This system uses a two-tier microservice architecture:

1. API Gateway (Flask, port 5000):
   - Main entry point for all client requests
   - Handles authentication and routing
   - Proxies API requests to the SyncService
   - Provides auto-recovery of the SyncService if it stops
   - Status monitoring and management endpoints

2. SyncService (FastAPI, port 8080):
   - Core business logic for synchronization
   - Implements change detection, transformation, validation
   - Provides detailed metrics and monitoring
   - Self-healing capabilities for failed syncs
   - Handles direct database interactions

Communication Flow:
-----------------
Client -> API Gateway (port 5000) -> SyncService (port 8080) -> External Systems

Port Configuration:
-----------------
- The main Flask application MUST run on port 5000
- The SyncService MUST run on port 8080 to avoid conflicts

This separation allows independent scaling, updating, and management of each component
while maintaining a unified API surface for clients.
"""
from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)