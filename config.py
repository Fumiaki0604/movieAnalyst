import json
import os
from pathlib import Path

PROFILE_PATH = Path(__file__).parent / "profile.json"


def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        return {}
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_profile(profile: dict):
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def profile_to_text(profile: dict) -> str:
    if not profile:
        return "プロフィール未設定"
    lines = [
        f"名前: {profile.get('name', '未設定')}",
        f"役割: {profile.get('role', '未設定')}",
        f"使用ツール: {', '.join(profile.get('tools', []))}",
        f"現在の関心: {profile.get('current_focus', '未設定')}",
        f"習熟度: {profile.get('expertise_level', '未設定')}",
        f"すでに知っている領域: {', '.join(profile.get('known_topics', []))}",
        f"目標: {', '.join(profile.get('goals', []))}",
    ]
    return "\n".join(lines)
