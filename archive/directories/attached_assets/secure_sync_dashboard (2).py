
from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from rbac_auth import get_current_user, check_permission
import pandas as pd
import os
import uuid
import hashlib
from datetime import datetime

app = FastAPI()

LOG_DIR = "logs"
STAGING_FILE = os.path.join(LOG_DIR, "staging_area.csv")
AUDIT_FILE = os.path.join(LOG_DIR, "approved_changes.csv")
ROLLBACK_FILE = os.path.join(LOG_DIR, "rollback_log.csv")
os.makedirs(LOG_DIR, exist_ok=True)

# Ensure base log files exist
for file_path, columns in [
    (STAGING_FILE, ["upload_id", "timestamp", "filename", "sha256", "prop_id", "status"]),
    (AUDIT_FILE, ["upload_id", "timestamp", "filename", "sha256", "prop_id", "status"]),
    (ROLLBACK_FILE, ["upload_id", "timestamp", "filename", "sha256", "prop_id", "status"])
]:
    if not os.path.exists(file_path):
        pd.DataFrame(columns=columns).to_csv(file_path, index=False)

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(user=Depends(check_permission("view"))):
    df = pd.read_csv(STAGING_FILE)
    rows = ""
    for _, row in df.iterrows():
        rows += f"<tr><td>{row['prop_id']}</td><td>{row['filename']}</td><td>{row['timestamp']}</td><td>{row['status']}</td>" + \
                f"<td><a href='/diff/{row['upload_id']}'>View Diff</a></td>"
        if user['role'] in ["Assessor", "ITAdmin"]:
            rows += f"<td><form method='post' action='/approve'><input type='hidden' name='upload_id' value='{row['upload_id']}'/>" + \
                    "<button type='submit'>Approve</button></form></td>"
        else:
            rows += "<td>—</td>"
    return f"""<html>
    <head><title>Sync Dashboard</title></head>
    <body>
    <h1>TerraFusionSync - Dashboard</h1>
    <p>User: {user['username']} | Role: {user['role']}</p>
    <form action='/upload' method='post' enctype='multipart/form-data'>
        Upload File: <input type='file' name='file'/>
        <button type='submit'>Submit</button>
    </form>
    <br><a href='/export'>Download Sync Log</a><br><br>
    <table border='1'>
    <tr><th>prop_id</th><th>Filename</th><th>Timestamp</th><th>Status</th><th>Diff</th><th>Action</th></tr>
    {rows}
    </table>
    <br>
    <h2>Rollback Approved Change</h2>
    <form method='post' action='/rollback'>
        Upload ID: <input type='text' name='upload_id'/>
        <button type='submit'>Rollback</button>
    </form>
    </body></html>"""

@app.post("/upload")
def upload(file: UploadFile = File(...), user=Depends(check_permission("upload"))):
    contents = file.file.read()
    sha = hashlib.sha256(contents).hexdigest()
    text = contents.decode("utf-8", errors="ignore")
    prop_id = "UNKNOWN"
    for line in text.splitlines():
        if "prop_id" in line.lower():
            prop_id = line.strip()
            break
    df = pd.read_csv(STAGING_FILE)
    new_row = pd.DataFrame([{
        "upload_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "filename": file.filename,
        "sha256": sha,
        "prop_id": prop_id,
        "status": "PENDING"
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(STAGING_FILE, index=False)
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/approve")
def approve(upload_id: str = Form(...), user=Depends(check_permission("approve"))):
    df = pd.read_csv(STAGING_FILE)
    df.loc[df['upload_id'] == upload_id, 'status'] = "APPROVED"
    df.to_csv(STAGING_FILE, index=False)
    approved = df[df['upload_id'] == upload_id]
    if os.path.exists(AUDIT_FILE):
        approved.to_csv(AUDIT_FILE, mode='a', header=False, index=False)
    else:
        approved.to_csv(AUDIT_FILE, index=False)
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/rollback")
def rollback(upload_id: str = Form(...), user=Depends(check_permission("rollback"))):
    df = pd.read_csv(AUDIT_FILE)
    if upload_id not in df['upload_id'].values:
        raise HTTPException(status_code=404, detail="Upload ID not found in audit log")
    match = df[df['upload_id'] == upload_id]
    df = df[df['upload_id'] != upload_id]
    df.to_csv(AUDIT_FILE, index=False)
    if os.path.exists(ROLLBACK_FILE):
        match.to_csv(ROLLBACK_FILE, mode="a", header=False, index=False)
    else:
        match.to_csv(ROLLBACK_FILE, index=False)
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/export")
def export():
    return RedirectResponse(url="/sync/export")
