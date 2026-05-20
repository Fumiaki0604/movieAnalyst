from __future__ import annotations

import asyncio
import json
import queue
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from config import load_profile
from graph import build_graph
from ingest import fetch_evidence_timeline

BASE = Path(__file__).parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


# ---- Pages ----

@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/player")
def player():
    return FileResponse(BASE / "static" / "player.html")


# ---- Reports ----

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


# ---- Profile ----

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


# ---- Analysis (SSE) ----

_STEP_INFO = {
    "extract_facts":   ("事実抽出中...",       35),
    "interpret":       ("解釈生成中...",        52),
    "analyze_issues":  ("問題点分析中...",      67),
    "generate_advice": ("アドバイス生成中...",  82),
    "summarize":       ("要約生成中...",        65),
    "compile_report":  ("レポート作成中...",    93),
}


def _run_analysis(url: str, mode: str, force: bool, q: queue.Queue) -> None:
    try:
        q.put({"type": "progress", "label": "字幕取得中...", "pct": 5})
        timeline, video_id = fetch_evidence_timeline(url)
        q.put({"type": "progress", "label": f"字幕取得完了（{len(timeline)}件）", "pct": 15})

        output_dir = BASE / "output"
        output_dir.mkdir(exist_ok=True)
        json_path = output_dir / f"report_{video_id}.json"

        if json_path.exists() and not force:
            q.put({"type": "done", "video_id": video_id})
            return

        profile = load_profile()
        graph = build_graph(mode=mode)

        initial_state = {
            "video_id": video_id,
            "video_url": url,
            "profile": profile,
            "evidence_timeline": timeline,
            "facts": [],
            "interpretations": [],
            "issues": [],
            "advice": [],
            "summary": "",
            "final_report": {},
        }

        q.put({"type": "progress", "label": "分析開始...", "pct": 20})

        final_state: dict = dict(initial_state)
        for event in graph.stream(initial_state, stream_mode="updates"):
            for node_name, updates in event.items():
                final_state.update(updates)
                label, pct = _STEP_INFO.get(node_name, (node_name, 88))
                q.put({"type": "progress", "label": label, "pct": pct})

        report = final_state.get("final_report", {})
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        q.put({"type": "done", "video_id": video_id})

    except Exception as e:
        q.put({"type": "error", "message": str(e)})


@app.get("/api/analyze/stream")
async def analyze_stream(url: str, mode: str = "full", force: str = "false"):
    force_bool = force.lower() == "true"
    q: queue.Queue = queue.Queue()
    threading.Thread(target=_run_analysis, args=(url, mode, force_bool, q), daemon=True).start()

    async def generator():
        loop = asyncio.get_event_loop()
        while True:
            try:
                msg = await loop.run_in_executor(None, lambda: q.get(timeout=600))
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                if msg["type"] in ("done", "error"):
                    break
            except Exception:
                yield f"data: {json.dumps({'type': 'error', 'message': 'タイムアウト'}, ensure_ascii=False)}\n\n"
                break

    return StreamingResponse(generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
