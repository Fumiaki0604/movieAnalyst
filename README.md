# 動画アナリスト

YouTubeの動画・ライブを字幕から分析し、視聴者プロフィールに合わせた「持ち帰りレポート」を生成するCLIツール。

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を記載
```

## 使い方

```bash
python -X utf8 main.py
```

URLを入力し、出力モードを選択するだけ。

## 出力モード

| モード | 内容 |
|--------|------|
| `full` | 視聴者プロフィールに合わせた持ち帰りレポート |
| `summary` | 3〜5行の要約のみ |
| `none` | 字幕取得のみ（分析なし） |

結果は `output_{video_id}.txt` に自動保存される。

## 視聴者プロフィール

`profile.json` を直接編集して自分の情報を設定する。
`full` モードのレポート精度に影響する。

## フェーズ

| フェーズ | 内容 | 状態 |
|---------|------|------|
| Phase 1 | YouTube視聴後レポート | 開発中 |
| Phase 2 | リアルタイム音声キャプチャ（Zoom・Meet対応） | 未着手 |
| Phase 3 | スライド解析（Claude Vision） | 未着手 |
| Phase 4 | デスクトップGUI | 未着手 |
