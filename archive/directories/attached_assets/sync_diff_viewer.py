
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
import os
import pandas as pd
import hashlib

app = FastAPI()
security = HTTPBearer()
AUTHORIZED_TOKEN = "secure-sync-token"
LOG_DIR = "logs"
STAGING_FILE = os.path.join(LOG_DIR, "staging_area.csv")
MOCK_PACS_FILE = os.path.join(LOG_DIR, "mock_pacs_data.csv")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != AUTHORIZED_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

def generate_mock_data():
    if not os.path.exists(MOCK_PACS_FILE):
        df = pd.DataFrame([
            {"prop_id": "10001", "land_value": 50000, "building_value": 120000, "tax_due": 3000},
            {"prop_id": "10002", "land_value": 60000, "building_value": 100000, "tax_due": 2900},
            {"prop_id": "10003", "land_value": 75000, "building_value": 90000, "tax_due": 3200}
        ])
        df.to_csv(MOCK_PACS_FILE, index=False)

@app.get("/sync/diff/{upload_id}", response_class=HTMLResponse)
def diff_upload(upload_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(credentials)
    generate_mock_data()
    
    if not os.path.exists(STAGING_FILE):
        raise HTTPException(status_code=404, detail="Staging file not found")
    
    staging_df = pd.read_csv(STAGING_FILE)
    if upload_id not in staging_df['upload_id'].values:
        raise HTTPException(status_code=404, detail="Upload ID not found")

    # Retrieve staging row
    row = staging_df[staging_df['upload_id'] == upload_id].iloc[0]
    prop_id = row['prop_id']
    sha256 = row['sha256']

    # Mocked new data derived from SHA256 (simulate changes)
    new_data = {
        "prop_id": prop_id,
        "land_value": int(sha256[0:2], 16) * 1000,
        "building_value": int(sha256[2:4], 16) * 1000,
        "tax_due": int(sha256[4:6], 16)
    }

    # Get mock current data
    mock_df = pd.read_csv(MOCK_PACS_FILE)
    current_row = mock_df[mock_df['prop_id'] == prop_id]
    if current_row.empty:
        raise HTTPException(status_code=404, detail=f"No current data for prop_id {prop_id}")
    current = current_row.iloc[0].to_dict()

    # Build diff HTML
    html = f"<h2>Diff Viewer for prop_id: {prop_id}</h2><table border='1'><tr><th>Field</th><th>Current</th><th>Proposed</th><th>Delta</th></tr>"
    for key in ['land_value', 'building_value', 'tax_due']:
        old = current.get(key, 0)
        new = new_data.get(key, 0)
        delta = new - old
        html += f"<tr><td>{key}</td><td>{old}</td><td>{new}</td><td>{delta}</td></tr>"
    html += "</table>"

    return HTMLResponse(html)
