#!/usr/bin/env python3
"""
Fixes the name conflict in the Market Analysis router where 'status' is used
both as an imported module and as a variable name.
"""

import re

router_path = "terrafusion_sync/plugins/market_analysis/router.py"

# Read the file
with open(router_path, "r") as f:
    content = f.read()

# Replace variable status with job_status
pattern1 = r"(\s+)status = str\(job\.status\) if job\.status else None"
replacement1 = r"\1job_status = str(job.status) if job.status else None"
content = re.sub(pattern1, replacement1, content)

# Replace status parameter with job_status in MarketAnalysisJobStatusResponse
pattern2 = r"(\s+)status=status,"
replacement2 = r"\1status=job_status,"
content = re.sub(pattern2, replacement2, content)

# Replace status parameter with job_status in MarketAnalysisJobResultResponse
pattern3 = r"(\s+)status=status,"
replacement3 = r"\1status=job_status,"
content = re.sub(pattern3, replacement3, content)

# Write the updated content back to the file
with open(router_path, "w") as f:
    f.write(content)

print("✅ Fixed name conflict in Market Analysis router.")