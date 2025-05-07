
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import pandas as pd
import os
import uuid
import hashlib
from datetime import datetime

app = FastAPI()

LOG_DIR = "logs"
STAGING_FILE = os.path.join(LOG_DIR, "staging_area.csv")
AUDIT_FILE = os.path.join(LOG_DIR, "approved_changes.csv")
os.makedirs(LOG_DIR, exist_ok=True)

# Ensure staging file exists
if not os.path.exists(STAGING_FILE):
    pd.DataFrame(columns=["upload_id", "timestamp", "filename", "sha256", "prop_id", "status"]).to_csv(STAGING_FILE, index=False)

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    df = pd.read_csv(STAGING_FILE)
    rows = ""
    for _, row in df.iterrows():
        rows += f"<tr><td>{row['prop_id']}</td><td>{row['filename']}</td><td>{row['timestamp']}</td><td>{row['status']}</td>" + \
                f"<td><a href='/diff/{row['upload_id']}'>View Diff</a></td>" + \
                f"<td><form method='post' action='/approve'><input type='hidden' name='upload_id' value='{row['upload_id']}'/>" + \
                "<button type='submit'>Approve</button></form></td></tr>"
    return f"""<html>
    <head><title>Sync Dashboard</title></head>
    <body>
    <h1>TerraFusionSync - Dashboard</h1>
    <form action='/upload' method='post' enctype='multipart/form-data'>
        Upload File: <input type='file' name='file'/>
        <button type='submit'>Submit</button>
    </form>
    <br><a href='/export'>Download Sync Log</a><br><br>
    <table border='1'>
    <tr><th>prop_id</th><th>Filename</th><th>Timestamp</th><th>Status</th><th>Diff</th><th>Action</th></tr>
    {rows}
    </table>
    </body></html>"""

@app.post("/upload")
def upload(file: UploadFile = File(...)):
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
def approve(upload_id: str = Form(...)):
    df = pd.read_csv(STAGING_FILE)
    df.loc[df['upload_id'] == upload_id, 'status'] = "APPROVED"
    df.to_csv(STAGING_FILE, index=False)
    approved = df[df['upload_id'] == upload_id]
    if os.path.exists(AUDIT_FILE):
        approved.to_csv(AUDIT_FILE, mode='a', header=False, index=False)
    else:
        approved.to_csv(AUDIT_FILE, index=False)
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/export")
def export():
    return HTMLResponse(f"<a href='/download/log'>Click to download log</a>")

@app.get("/download/log")
def download():
    return RedirectResponse(url="/sync/export")

@app.get("/diff/{upload_id}", response_class=HTMLResponse)
def diff(upload_id: str):
    df = pd.read_csv(STAGING_FILE)
    row = df[df['upload_id'] == upload_id]
    if row.empty:
        return HTMLResponse("<h3>No record found</h3>")
    prop_id = row.iloc[0]['prop_id']
    sha = row.iloc[0]['sha256']
    mock = {
        "prop_id": prop_id,
        "land_value": 50000,
        "building_value": 100000,
        "tax_due": 3000
    }
    proposed = {
        "land_value": int(sha[0:2], 16) * 1000,
        "building_value": int(sha[2:4], 16) * 1000,
        "tax_due": int(sha[4:6], 16)
    }
    table = f"<table border='1'><tr><th>Field</th><th>Current</th><th>Proposed</th><th>Delta</th></tr>"
    for k in proposed:
        delta = proposed[k] - mock.get(k, 0)
        table += f"<tr><td>{k}</td><td>{mock[k]}</td><td>{proposed[k]}</td><td>{delta}</td></tr>"
    table += "</table>"
    return HTMLResponse(f"<h3>Diff for {prop_id}</h3>" + table)
