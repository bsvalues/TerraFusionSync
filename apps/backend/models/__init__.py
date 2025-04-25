"""
Models package for the TerraFusion SyncService platform.

This package contains SQLAlchemy model definitions for the Flask application.
"""

# Import models when available in production
try:
    from .sync_pair import SyncPair
    from .sync_operation import SyncOperation, SyncOperationDetails
    from .audit import AuditEntry
    from .system_metrics import SystemMetrics
except ImportError:
    # Fallback for development - use models from the parent package
    pass