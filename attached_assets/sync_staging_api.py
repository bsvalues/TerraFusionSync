
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
import os
import pandas as pd
import hashlib
from datetime import datetime
import uuid

app = FastAPI()
security = HTTPBearer()
AUTHORIZED_TOKEN = "secure-sync-token"
LOG_DIR = "logs"
STAGING_FILE = os.path.join(LOG_DIR, "staging_area.csv")
AUDIT_FILE = os.path.join(LOG_DIR, "approved_changes.csv")
os.makedirs(LOG_DIR, exist_ok=True)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != AUTHORIZED_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

def write_to_staging(file: UploadFile, contents: bytes, prop_id: str):
    row = {
        "upload_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "filename": file.filename,
        "sha256": hashlib.sha256(contents).hexdigest(),
        "prop_id": prop_id,
        "status": "PENDING"
    }
    df = pd.DataFrame([row])
    if os.path.exists(STAGING_FILE):
        df.to_csv(STAGING_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(STAGING_FILE, index=False)

@app.post("/sync/stage")
def stage_upload(file: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(credentials)
    contents = file.file.read()
    text = contents.decode("utf-8", errors="ignore")
    prop_id = None
    if "prop_id" in text.lower():
        lines = text.splitlines()
        for line in lines:
            if "prop_id" in line.lower():
                prop_id = line.strip()
                break
    prop_id = prop_id or "UNKNOWN"
    write_to_staging(file, contents, prop_id)
    return {"status": "staged", "filename": file.filename, "prop_id": prop_id}

@app.get("/sync/staging", response_class=HTMLResponse)
def view_staging(credentials: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(credentials)
    if not os.path.exists(STAGING_FILE):
        return HTMLResponse("<h3>No staged records</h3>")
    df = pd.read_csv(STAGING_FILE)
    return HTMLResponse(df.to_html(index=False))

@app.post("/sync/approve/{upload_id}")
def approve_upload(upload_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(credentials)
    if not os.path.exists(STAGING_FILE):
        raise HTTPException(status_code=404, detail="Staging file missing")
    df = pd.read_csv(STAGING_FILE)
    if upload_id not in df['upload_id'].values:
        raise HTTPException(status_code=404, detail="Upload ID not found")
    df.loc[df['upload_id'] == upload_id, 'status'] = "APPROVED"
    df.to_csv(STAGING_FILE, index=False)

    approved_row = df[df['upload_id'] == upload_id]
    if os.path.exists(AUDIT_FILE):
        approved_row.to_csv(AUDIT_FILE, mode='a', header=False, index=False)
    else:
        approved_row.to_csv(AUDIT_FILE, index=False)
    
    return {"status": "approved", "upload_id": upload_id}
