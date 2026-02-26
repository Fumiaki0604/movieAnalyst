import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


def extract_video_id(url: str) -> str | None:
    patterns = [
        r"youtube\.com/watch\?v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"youtube\.com/live/([^?]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_transcript(url: str) -> tuple[str, str]:
    """
    Returns: (transcript_text, video_id)
    Raises: ValueError if transcript unavailable
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"YouTubeのURLから動画IDを取得できませんでした: {url}")

    try:
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)

        # 日本語字幕を優先、なければ英語、なければ最初に見つかったもの
        transcript = None
        for lang in ["ja", "en"]:
            try:
                transcript = transcript_list.find_transcript([lang])
                break
            except NoTranscriptFound:
                continue

        if transcript is None:
            # 自動生成字幕を含む最初のものを使用
            transcript = next(iter(transcript_list))

        entries = transcript.fetch()
        text = " ".join(e.text for e in entries)
        return text, video_id

    except TranscriptsDisabled:
        raise ValueError("この動画は字幕が無効になっています")
    except NoTranscriptFound:
        raise ValueError("利用可能な字幕が見つかりませんでした")
    except StopIteration:
        raise ValueError("利用可能な字幕が見つかりませんでした")
