"""
Self-Healing package for the SyncService.

This package provides capabilities for automatic detection and recovery
of failures in sync operations with progressive retry strategies.
"""

from .orchestrator import SelfHealingOrchestrator, FailureCategory

__all__ = ['SelfHealingOrchestrator', 'FailureCategory']