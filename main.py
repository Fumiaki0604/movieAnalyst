from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser

from dotenv import load_dotenv

load_dotenv()

PORT = 8765
BANNER = """
╔══════════════════════════════════════════════╗
║   動画アナリスト v2.0  (LangGraph edition)   ║
╚══════════════════════════════════════════════╝
"""


def main() -> None:
    print(BANNER)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("エラー: ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    from server import app as server_app
    import uvicorn

    def _run():
        uvicorn.run(server_app, host="127.0.0.1", port=PORT, log_level="error")

    threading.Thread(target=_run, daemon=True).start()
    time.sleep(1.2)

    url = f"http://127.0.0.1:{PORT}"
    webbrowser.open(url)
    print(f"ブラウザで開きました: {url}")
    print("Ctrl+C で終了します。")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\n終了しました。")


if __name__ == "__main__":
    main()
