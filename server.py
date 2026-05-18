from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/player")
def player():
    return FileResponse(BASE / "static" / "player.html")


@app.get("/api/reports")
def list_reports():
    output_dir = BASE / "output"
    if not output_dir.exists():
        return JSONResponse([])
    reports = []
    for path in sorted(output_dir.glob("report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            reports.append({
                "video_id": data.get("video_id", ""),
                "video_url": data.get("video_url", ""),
                "summary": data.get("summary", ""),
                "fact_count": len(data.get("facts", [])),
                "advice_count": len(data.get("advice", [])),
                "mtime": path.stat().st_mtime,
            })
        except Exception:
            continue
    return JSONResponse(reports)


@app.get("/api/report/{video_id}")
def get_report(video_id: str):
    path = BASE / "output" / f"report_{video_id}.json"
    if not path.exists():
        return JSONResponse({"error": "report not found"}, status_code=404)
    return JSONResponse(json.loads(path.read_text(encoding="utf-8")))


@app.get("/api/profile")
def get_profile():
    path = BASE / "profile.json"
    if not path.exists():
        return JSONResponse({})
    return JSONResponse(json.loads(path.read_text(encoding="utf-8")))


@app.put("/api/profile")
async def put_profile(request: Request):
    data = await request.json()
    path = BASE / "profile.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return JSONResponse({"ok": True})
