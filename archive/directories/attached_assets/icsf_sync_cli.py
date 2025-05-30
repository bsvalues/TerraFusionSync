
import requests
import argparse
import os

BASE_URL = "http://localhost:8000"
TOKEN = "secure-sync-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def list_staged():
    res = requests.get(f"{BASE_URL}/sync/staging", headers=HEADERS)
    print(res.text)

def approve(upload_id):
    res = requests.post(f"{BASE_URL}/sync/approve/{upload_id}", headers=HEADERS)
    print(res.json())

def diff(upload_id):
    print(f"Open in browser: {BASE_URL}/sync/diff/{upload_id}")

def upload_file(filepath):
    with open(filepath, "rb") as f:
        files = {'file': (os.path.basename(filepath), f, 'application/xml')}
        res = requests.post(f"{BASE_URL}/sync/stage", files=files, headers=HEADERS)
        print(res.json())

def export_logs():
    res = requests.get(f"{BASE_URL}/sync/export", headers=HEADERS)
    with open("exported_sync_log.csv", "wb") as f:
        f.write(res.content)
    print("Exported to exported_sync_log.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ICSF Sync Workflow CLI")
    parser.add_argument("--upload", type=str, help="Upload a file for staging")
    parser.add_argument("--list", action="store_true", help="List staged files")
    parser.add_argument("--approve", type=str, help="Approve an upload by ID")
    parser.add_argument("--diff", type=str, help="Launch diff view for an upload")
    parser.add_argument("--export", action="store_true", help="Export logs to CSV")
    args = parser.parse_args()

    if args.upload:
        upload_file(args.upload)
    if args.list:
        list_staged()
    if args.approve:
        approve(args.approve)
    if args.diff:
        diff(args.diff)
    if args.export:
        export_logs()
