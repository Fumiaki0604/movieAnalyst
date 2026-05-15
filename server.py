from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "player.html")


@app.get("/api/report/{video_id}")
def get_report(video_id: str):
    path = BASE / "output" / f"report_{video_id}.json"
    if not path.exists():
        return JSONResponse({"error": "report not found"}, status_code=404)
    return JSONResponse(json.loads(path.read_text(encoding="utf-8")))
