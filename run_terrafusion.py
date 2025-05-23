"""
TerraFusion Platform - Run Script

This script starts the TerraFusion Platform on port 5001 to avoid conflicts.
"""

import os
from main import app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True)