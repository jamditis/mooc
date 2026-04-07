"""Extract frames at 3-second intervals from all downloaded videos."""

import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METADATA_FILE = BASE_DIR / "metadata.json"
FRAMES_DIR = BASE_DIR / "frames"


def extract_frames(video_path: Path, platform: str, video_id: str) -> int:
    """Extract frames from a single video. Returns number of frames extracted."""
    out_dir = FRAMES_DIR / platform / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    existing = list(out_dir.glob("frame_*.jpg"))
    if existing:
        print(f"  SKIP (already done, {len(existing)} frames): {video_id}")
        return len(existing)

    if not video_path.exists():
        print(f"  MISSING: {video_path}")
        return 0

    # ffmpeg: extract 1 frame every 3 seconds, scale to max 1920px wide, JPEG 95% quality
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", "fps=1/3,scale='min(1920,iw)':-1",
        "-q:v", "2",
        "-start_number", "0",
        str(out_dir / "frame_%04d.jpg"),
        "-y",
        "-loglevel", "error",
    ]

    try:
        subprocess.run(cmd, check=True, timeout=120)
        # frame_0000.jpg = 0s, frame_0001.jpg = 3s, frame_0002.jpg = 6s, etc.
        frames = list(out_dir.glob("frame_*.jpg"))
        print(f"  OK: {len(frames)} frames from {video_id}")
        return len(frames)

    except subprocess.CalledProcessError as e:
        print(f"  FAILED: {video_id}: {e}")
        return 0
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {video_id}")
        return 0


def main():
    with open(METADATA_FILE) as f:
        metadata = json.load(f)

    platforms_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    videos = metadata["videos"]
    if platforms_filter:
        videos = [v for v in videos if v["platform"] in platforms_filter]

    print(f"Extracting frames from {len(videos)} videos at 3-second intervals.\n")

    total_frames = 0
    for i, video in enumerate(videos, 1):
        video_path = BASE_DIR / video["local_path"]
        platform = video["platform"]
        video_id = video["id"]
        title = video.get("title", video_id)[:50]

        print(f"[{i}/{len(videos)}] {platform}/{title}")
        total_frames += extract_frames(video_path, platform, video_id)

    print(f"\nDone. {total_frames} total frames extracted.")


if __name__ == "__main__":
    main()
