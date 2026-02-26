import os
import sys
import io
from dotenv import load_dotenv

load_dotenv()

# Windowsのコンソール出力をUTF-8に設定
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from config import load_profile
from fetcher import fetch_transcript
from analyst import analyze, OUTPUT_MODES

BANNER = """
╔══════════════════════════════════╗
║      動画アナリスト v0.1         ║
╚══════════════════════════════════╝
"""


def select_mode() -> str:
    print("\n【出力モードを選択してください】")
    for key, desc in OUTPUT_MODES.items():
        print(f"  {key}: {desc}")
    print()

    while True:
        choice = input("モード (full / summary / none) [full]: ").strip().lower()
        if choice == "":
            return "full"
        if choice in OUTPUT_MODES:
            return choice
        print("full / summary / none のいずれかを入力してください")


def main():
    print(BANNER)

    # APIキー確認
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("エラー: ANTHROPIC_API_KEY が設定されていません")
        print(".env ファイルに ANTHROPIC_API_KEY=sk-ant-... を記載してください")
        sys.exit(1)

    # プロフィール読み込み
    profile = load_profile()
    if profile:
        print(f"プロフィール読み込み済み: {profile.get('name', '')} / {profile.get('role', '')}")

    # URL入力
    url = input("\nYouTube URLを入力してください: ").strip()
    if not url:
        print("URLが入力されていません")
        sys.exit(1)

    # 出力モード選択
    mode = select_mode()

    if mode == "none":
        print("\n字幕取得のみ実行します...")

    # 字幕取得
    print("\n字幕を取得中...")
    try:
        transcript, video_id = fetch_transcript(url)
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)

    print(f"取得完了: {len(transcript)} 文字 (動画ID: {video_id})")

    if mode == "none":
        print("\n--- 字幕（先頭500文字） ---")
        print(transcript[:500])
        return

    # 分析
    print(f"\n分析中 (モード: {mode})...")
    result = analyze(transcript, profile, mode)

    print("\n" + "=" * 50)
    print(result)
    print("=" * 50)

    # 結果をファイルに保存
    output_path = f"output_{video_id}.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"モード: {mode}\n\n")
        f.write(result)
    print(f"\n結果を保存しました: {output_path}")


if __name__ == "__main__":
    main()
