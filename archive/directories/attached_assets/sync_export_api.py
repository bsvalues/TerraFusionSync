
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, HTMLResponse
import os
import pandas as pd

app = FastAPI()
security = HTTPBearer()
LOG_FILE = "logs/sync_import_log.csv"
AUTHORIZED_TOKEN = "secure-sync-token"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != AUTHORIZED_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

@app.get("/sync/export", response_class=FileResponse)
def export_logs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(credentials)
    if not os.path.exists(LOG_FILE):
        raise HTTPException(status_code=404, detail="No log file found")
    return FileResponse(LOG_FILE, filename="sync_import_log.csv", media_type="text/csv")

@app.get("/sync/logs", response_class=HTMLResponse)
def view_logs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(credentials)
    if not os.path.exists(LOG_FILE):
        return HTMLResponse("<h3>No logs available</h3>")
    
    df = pd.read_csv(LOG_FILE)
    html = df.to_html(index=False)
    return HTMLResponse(f"""<html><head><title>Sync Logs</title></head><body>{html}</body></html>""")
