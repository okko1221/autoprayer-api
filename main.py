from fastapi import FastAPI
from pydantic import BaseModel
import time
import json
import os

# ✅ 修正成絕對路徑（支援 Render 等部署平台）
DB_PATH = os.path.join(os.path.dirname(__file__), "devices.json")

app = FastAPI()
TRIAL_DURATION = 1800  # 30分鐘

# === 資料模型 ===
class AuthRequest(BaseModel):
    serial: str

def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f)

@app.post("/check")
async def check_license(req: AuthRequest):
    serial = req.serial.strip().replace(" ", "").replace(".", "").lower()

    db = load_db()

    if serial in db:
        record = db[serial]
        if record.get("licensed"):
            return {"status": "authorized"}

        start = record.get("trial_start")
        if start:
            elapsed = time.time() - start
            if elapsed < TRIAL_DURATION:
                return {"status": "trial", "remaining": int(TRIAL_DURATION - elapsed)}
            else:
                return {"status": "expired"}

    # 新用戶：寫入 trial_start
    db[serial] = {"licensed": False, "trial_start": time.time()}
    save_db(db)
    return {"status": "trial", "remaining": TRIAL_DURATION}
