#!/usr/bin/env python3
"""
TerraFusion Platform Command Line Interface

This is the main entry point for the TerraFusion CLI tools.
"""
import sys
import os
from pathlib import Path

# Add the project root to sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(PROJECT_ROOT))

if __name__ == "__main__":
    from terrafusion_platform.sdk.cli import main
    main()