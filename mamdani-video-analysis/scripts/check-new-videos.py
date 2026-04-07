"""Check YouTube and TikTok for new Mamdani videos (metadata only, no downloads).

This script is designed for GitHub Actions or any environment where you want
to detect new videos without downloading them. It uses yt-dlp's --flat-playlist
flag to quickly list videos on a channel, then compares against metadata.json.

Usage:
    python scripts/check-new-videos.py                # check youtube + tiktok
    python scripts/check-new-videos.py youtube         # check one platform
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METADATA_FILE = BASE_DIR / "metadata.json"

SOURCES = {
    "youtube": "https://www.youtube.com/@ZohranforNYC/videos",
    "tiktok": "https://www.tiktok.com/@zohran_k_mamdani",
}


def get_known_ids() -> set:
    """Load existing video IDs from metadata.json."""
    with open(METADATA_FILE, encoding="utf-8") as f:
        metadata = json.load(f)
    return {v["id"] for v in metadata["videos"]}


def check_platform(platform: str, url: str) -> list[dict]:
    """Use yt-dlp --flat-playlist to list videos without downloading.

    --flat-playlist tells yt-dlp to only fetch the playlist page and extract
    basic info (id, title, url) without downloading or processing each video.
    This is much faster and uses almost no bandwidth.
    """
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--playlist-items", "1:15",
        "--dump-single-json",
        "--no-warnings",
        url,
    ]

    print(f"Checking {platform}: {url}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            print(f"  WARN: yt-dlp exited {result.returncode}")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[-3:]:
                    print(f"  stderr: {line}")
            return []

        data = json.loads(result.stdout)
        entries = data.get("entries", [])

        videos = []
        for entry in entries:
            videos.append({
                "id": str(entry.get("id", "")),
                "title": entry.get("title", ""),
                "url": entry.get("url", entry.get("webpage_url", "")),
                "duration": entry.get("duration") or 0,
            })

        print(f"  Found {len(videos)} videos listed on {platform}")
        return videos

    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {platform} check took over 2 minutes")
        return []
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  ERROR: Failed to parse {platform} response: {e}")
        return []


def format_date(date_str: str) -> str:
    """Convert yt-dlp date (YYYYMMDD) to ISO 8601."""
    if date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return date_str or datetime.now().strftime("%Y-%m-%d")


def main():
    platforms = sys.argv[1:] if len(sys.argv) > 1 else list(SOURCES.keys())
    known_ids = get_known_ids()

    print(f"Known videos: {len(known_ids)}")
    print(f"Checking: {', '.join(platforms)}")
    print()

    new_videos = []

    for platform in platforms:
        if platform not in SOURCES:
            print(f"Unknown platform: {platform}")
            continue

        listed = check_platform(platform, SOURCES[platform])
        for v in listed:
            if v["id"] and v["id"] not in known_ids:
                new_videos.append({
                    "id": v["id"],
                    "title": v["title"],
                    "upload_date": datetime.now().strftime("%Y-%m-%d"),
                    "duration": v["duration"],
                    "source_url": v["url"],
                    "platform": platform,
                    "local_path": "",
                    "description": v["title"],
                    "_needs_download": True,
                })
                known_ids.add(v["id"])

    print()

    if new_videos:
        # Add new entries to metadata.json
        with open(METADATA_FILE, encoding="utf-8") as f:
            metadata = json.load(f)

        for v in new_videos:
            metadata["videos"].append(v)

        metadata["videos"].sort(key=lambda v: v.get("upload_date", ""), reverse=True)

        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print(f"NEW VIDEOS FOUND: {len(new_videos)}")
        for v in new_videos:
            print(f"  [{v['platform']}] {v['title'][:60]}")
        print(f"\nmetadata.json updated ({len(metadata['videos'])} total videos)")
    else:
        print("No new videos found.")


if __name__ == "__main__":
    main()
