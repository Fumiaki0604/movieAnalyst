from __future__ import annotations

import io
import json
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from config import load_profile
from graph import build_graph
from ingest import extract_video_id, fetch_evidence_timeline

BANNER = """
╔══════════════════════════════════════════════╗
║   動画アナリスト v2.0  (LangGraph edition)   ║
╚══════════════════════════════════════════════╝
"""

PORT = 8765


def _fmt_time(sec: float) -> str:
    m, s = int(sec // 60), int(sec % 60)
    return f"{m:02d}:{s:02d}"


def print_report(report: dict) -> None:
    print("\n" + "=" * 58)
    print(f"  {report.get('summary', '')}")
    print("=" * 58)

    if report.get("facts"):
        print("\n【主要事実】")
        for f in report["facts"]:
            ts = f.get("timestamp_start")
            ts_str = f" @ {_fmt_time(ts)}" if ts is not None else ""
            print(f"  - {f['label']}{ts_str}")
            print(f"    {f['description']}")

    if report.get("interpretations"):
        print("\n【解釈】")
        for i in report["interpretations"]:
            print(f"  - {i['label']}")
            print(f"    {i['explanation']}")

    if report.get("issues"):
        print("\n【問題点・課題】")
        for iss in report["issues"]:
            sev = iss.get("severity", "?").upper()
            print(f"  - [{sev}] {iss['label']}")
            print(f"    {iss['description']}")

    if report.get("advice"):
        print("\n【アドバイス】")
        for idx, adv in enumerate(report["advice"], 1):
            pri = adv.get("priority", "?").upper()
            print(f"  {idx}. [{pri}] {adv['title']}")
            print(f"     アクション : {adv['action']}")
            print(f"     場面       : {adv['context']}")
            print(f"     確認方法   : {adv['measure']}")
    print()


def launch_player(video_id: str) -> None:
    from server import app as server_app
    import uvicorn

    def _run():
        uvicorn.run(server_app, host="127.0.0.1", port=PORT, log_level="error")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(1.2)

    url = f"http://127.0.0.1:{PORT}/player?video_id={video_id}"
    webbrowser.open(url)
    print(f"ブラウザで開きました: {url}")
    print("Ctrl+C で終了します。")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\n終了しました。")


def main() -> None:
    print(BANNER)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("エラー: ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    profile = load_profile()
    if profile:
        print(f"プロフィール: {profile.get('name', '')} / {profile.get('role', '')}")

    url = input("\nYouTube URL を入力してください: ").strip()
    if not url:
        print("URL が入力されていません")
        sys.exit(1)

    # video_id を先に取得（字幕フェッチなし）
    video_id = extract_video_id(url)
    if not video_id:
        print("エラー: URLから動画IDを取得できませんでした")
        sys.exit(1)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    json_path = output_dir / f"report_{video_id}.json"

    # 既存レポートがあれば再生成を確認
    if json_path.exists():
        print(f"\n既存レポートがあります: {json_path}")
        choice = input("  [1] 既存を使う  [2] 再分析する > ").strip()
        if choice != "2":
            report = json.loads(json_path.read_text(encoding="utf-8"))
            print_report(report)
            launch_player(video_id)
            return

    # 出力モード選択
    print("\n出力モードを選択してください:")
    print("  [1] full    - プロフィール対応の詳細レポート（デフォルト）")
    print("  [2] summary - 3〜5文の要約のみ")
    print("  [3] none    - 字幕取得のみ（分析なし）")
    mode_input = input("  モード [1/2/3] > ").strip()
    mode = {"2": "summary", "3": "none"}.get(mode_input, "full")
    print(f"モード: {mode}")

    # 字幕取得
    print("\nエビデンスタイムライン取得中...")
    try:
        timeline, video_id = fetch_evidence_timeline(url)
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    print(f"取得完了: {len(timeline)} エントリ (動画ID: {video_id})")

    # LangGraph 実行
    print("\nマルチエージェント分析開始:")
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

    final_state: dict = dict(initial_state)
    for event in graph.stream(initial_state, stream_mode="updates"):
        for _, updates in event.items():
            final_state.update(updates)

    report = final_state.get("final_report", {})
    print_report(report)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"JSON レポート保存: {json_path}")

    launch_player(video_id)


if __name__ == "__main__":
    main()
