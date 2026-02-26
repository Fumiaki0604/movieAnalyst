import anthropic
from config import profile_to_text

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

# 出力モード定義
OUTPUT_MODES = {
    "full": "視聴後レポート（持ち帰り整理）を生成する",
    "summary": "要約だけ生成する（レポートなし）",
    "none": "何も生成しない（字幕取得のみ）",
}


def analyze(transcript: str, profile: dict, mode: str = "full") -> str:
    if mode == "none":
        return ""

    profile_text = profile_to_text(profile)

    if mode == "summary":
        prompt = f"""以下の動画の内容を3〜5行で要約してください。

【動画の書き起こし】
{transcript[:8000]}
"""
    else:  # full
        prompt = f"""あなたは、セミナー・動画の内容を視聴者の背景に合わせて整理する専門家です。

【視聴者のプロフィール】
{profile_text}

【動画の書き起こし】
{transcript[:8000]}

---

以下の形式で「視聴後レポート」を作成してください。

## 今すぐ適用できること
（視聴者の現状に照らして、明日から実践できる具体的なアクションを優先度順に3〜5点）

## 知識として持っておくこと
（すぐには使わないが、知っておく価値がある概念・考え方）

## スキップしていいこと
（視聴者がすでに知っている、または今は不要な内容）

## 一言まとめ
（この動画を一文で表すなら）

---
制約:
- 「今すぐ適用」は具体的に。「〜を意識する」ではなく「〜をCLAUDE.mdに追記する」レベルで
- 視聴者がすでに知っていることは繰り返さない
- 長くしない。各項目は2〜3行以内
"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
