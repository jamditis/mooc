"""Transcribe all downloaded videos using Whisper large-v3 on GPU."""

import json
import sys
import time
from pathlib import Path

import torch
import whisper

BASE_DIR = Path(__file__).resolve().parent.parent
METADATA_FILE = BASE_DIR / "metadata.json"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"


def transcribe_video(model, video_path: Path, platform: str, video_id: str) -> bool:
    """Transcribe a single video. Returns True if successful."""
    out_dir = TRANSCRIPTS_DIR / platform
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"{video_id}.json"
    txt_path = out_dir / f"{video_id}.txt"

    if json_path.exists() and txt_path.exists():
        print(f"  SKIP (already done): {video_id}")
        return True

    if not video_path.exists():
        print(f"  MISSING: {video_path}")
        return False

    print(f"  Transcribing: {video_path.name} ...", end="", flush=True)
    start = time.time()

    try:
        result = model.transcribe(
            str(video_path),
            language="en",
            word_timestamps=True,
            verbose=False,
        )

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result["text"].strip())

        elapsed = time.time() - start
        word_count = len(result["text"].split())
        print(f" done ({elapsed:.1f}s, {word_count} words)")
        return True

    except Exception as e:
        elapsed = time.time() - start
        print(f" FAILED ({elapsed:.1f}s): {e}")
        return False


def main():
    with open(METADATA_FILE) as f:
        metadata = json.load(f)

    platforms_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    videos = metadata["videos"]
    if platforms_filter:
        videos = [v for v in videos if v["platform"] in platforms_filter]

    model_name = "turbo"
    print(f"Loading Whisper {model_name} on CUDA...")
    model = whisper.load_model(model_name, device="cuda")
    print(f"Model loaded. Transcribing {len(videos)} videos.\n")

    success = 0
    failed = 0

    for i, video in enumerate(videos, 1):
        video_path = BASE_DIR / video["local_path"]
        platform = video["platform"]
        video_id = video["id"]
        title = video.get("title", video_id)[:50]

        print(f"[{i}/{len(videos)}] {platform}/{title}")
        if transcribe_video(model, video_path, platform, video_id):
            success += 1
        else:
            failed += 1

    del model
    torch.cuda.empty_cache()

    print(f"\nDone. {success} transcribed, {failed} failed.")


if __name__ == "__main__":
    main()
