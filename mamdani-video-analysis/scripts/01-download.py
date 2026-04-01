"""Download videos from Mamdani's social media accounts using yt-dlp."""

import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
METADATA_FILE = BASE_DIR / "metadata.json"

SOURCES = {
    "youtube": {
        "url": "https://www.youtube.com/@ZohranforNYC/videos",
        "playlist_items": "1:15",
    },
    "twitter": {
        "url": "https://twitter.com/ZohranKMamdani/media",
        "playlist_items": "1:15",
    },
    "tiktok": {
        "url": "https://www.tiktok.com/@zohran_k_mamdani",
        "playlist_items": "1:15",
    },
    "instagram": {
        "url": "https://www.instagram.com/nycmayor/",
        "playlist_items": "1:15",
    },
    "facebook": {
        "url": "https://www.facebook.com/NYCMayor/reels/",
        "playlist_items": "1:15",
    },
}


def download_platform(platform: str, config: dict) -> list[dict]:
    """Download videos for a single platform. Returns list of video metadata dicts."""
    out_dir = DOWNLOADS_DIR / platform
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--playlist-items", config["playlist_items"],
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
        "--merge-output-format", "mp4",
        "-o", str(out_dir / "%(id)s.%(ext)s"),
        "--write-info-json",
        "--no-write-playlist-metafiles",
        "--no-overwrites",
        "--ignore-errors",
        "--print-json",
        config["url"],
    ]

    print(f"\n{'='*60}")
    print(f"Downloading {platform}: {config['url']}")
    print(f"{'='*60}")

    videos = []
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )

        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                info = json.loads(line)
                video_file = out_dir / f"{info['id']}.mp4"
                if not video_file.exists():
                    matches = list(out_dir.glob(f"{info['id']}.*"))
                    matches = [m for m in matches if m.suffix != ".json"]
                    video_file = matches[0] if matches else video_file

                videos.append({
                    "id": info.get("id", ""),
                    "title": info.get("title", ""),
                    "upload_date": _format_date(info.get("upload_date", "")),
                    "duration": info.get("duration") or 0,
                    "source_url": info.get("webpage_url", config["url"]),
                    "platform": platform,
                    "local_path": str(video_file.relative_to(BASE_DIR)),
                    "description": info.get("description", ""),
                })
                title = info.get('title', info.get('id', '?'))[:60]
                print(f"  OK: {title}".encode('ascii', errors='replace').decode('ascii'))
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

        if result.returncode != 0 and not videos:
            print(f"  WARN: yt-dlp exited {result.returncode}")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[-5:]:
                    print(f"  stderr: {line}".encode('ascii', errors='replace').decode('ascii'))

    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {platform} download took over 10 minutes")

    print(f"  Downloaded {len(videos)} videos from {platform}")
    return videos


def _format_date(date_str: str) -> str:
    """Convert yt-dlp date format (YYYYMMDD) to ISO 8601."""
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return date_str


def main():
    platforms = sys.argv[1:] if len(sys.argv) > 1 else list(SOURCES.keys())

    with open(METADATA_FILE) as f:
        metadata = json.load(f)

    existing_ids = {v["id"] for v in metadata["videos"]}

    for platform in platforms:
        if platform not in SOURCES:
            print(f"Unknown platform: {platform}")
            continue
        videos = download_platform(platform, SOURCES[platform])
        for v in videos:
            if v["id"] not in existing_ids:
                metadata["videos"].append(v)
                existing_ids.add(v["id"])

    metadata["videos"].sort(key=lambda v: v["upload_date"], reverse=True)

    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    total = len(metadata["videos"])
    print(f"\nDone. {total} total videos in metadata.json")


if __name__ == "__main__":
    main()
