from __future__ import annotations

import re
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled


def extract_video_id(url: str) -> Optional[str]:
    patterns = [
        r"youtube\.com/watch\?v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"youtube\.com/live/([^?]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def _attr(entry, key: str, default=0.0):
    """dict / object どちらにも対応するアクセサ。"""
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def fetch_evidence_timeline(url: str) -> tuple[list[dict], str]:
    """
    YouTube 字幕を取得し EvidenceTimeline 形式に変換する。

    Returns:
        (timeline, video_id)
        各 timeline エントリ: {event_id, start, end, modality, text, confidence}

    NOTE: Azure AI Video Indexer への切り替えは、この関数を差し替えるだけで対応できる。
    Video Indexer は transcript 以外に ocr / shot / audio_effect 等の
    modality も返せるため、同一スキーマで受け取れるよう設計している。
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"URLから動画IDを取得できませんでした: {url}")

    try:
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)

        transcript = None
        for lang in ["ja", "en"]:
            try:
                transcript = transcript_list.find_transcript([lang])
                break
            except NoTranscriptFound:
                continue

        if transcript is None:
            transcript = next(iter(transcript_list))

        entries = transcript.fetch()

        timeline: list[dict] = []
        for i, entry in enumerate(entries):
            start = float(_attr(entry, "start", 0.0))
            duration = float(_attr(entry, "duration", 3.0))
            text = str(_attr(entry, "text", ""))
            timeline.append(
                {
                    "event_id": f"t{i:04d}",
                    "start": start,
                    "end": start + duration,
                    "modality": "transcript",
                    "text": text,
                    "confidence": 1.0,
                }
            )

        return timeline, video_id

    except TranscriptsDisabled:
        raise ValueError("この動画は字幕が無効になっています")
    except NoTranscriptFound:
        raise ValueError("利用可能な字幕が見つかりませんでした")
    except StopIteration:
        raise ValueError("利用可能な字幕が見つかりませんでした")
