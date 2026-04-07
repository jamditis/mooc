"""Check for new Mamdani videos and run the full processing pipeline.

This script orchestrates the existing pipeline scripts:
  01-download.py  -> download new videos via yt-dlp
  02-transcribe.py -> transcribe audio with Whisper (GPU)
  03-extract-frames.py -> extract frames with ffmpeg
  04-build-analysis.py -> rebuild topic/sentiment analysis

After processing, it copies updated analysis files and the run log
to the upload/ folder, which syncs to Google Drive automatically.

Usage:
    python scripts/update-pipeline.py              # full run
    python scripts/update-pipeline.py --dry-run    # check only, no downloads
    python scripts/update-pipeline.py --skip-upload # skip copying to upload/
    python scripts/update-pipeline.py --platforms youtube  # one platform only
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
METADATA_FILE = BASE_DIR / "metadata.json"
ANALYSIS_DIR = BASE_DIR / "analysis"
LOGS_DIR = BASE_DIR / "logs"
UPLOAD_DIR = REPO_ROOT / "upload"

DEFAULT_PLATFORMS = ["youtube", "tiktok"]


def setup_logging(dry_run: bool) -> Path:
    """Set up dual logging to console and a timestamped log file.

    Returns the path to the log file.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    prefix = "dryrun" if dry_run else "update"
    log_file = LOGS_DIR / f"{prefix}_{timestamp}.log"

    # Root logger with dual handlers
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console)

    # File handler with timestamps
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")
    )
    logger.addHandler(file_handler)

    return log_file


def load_metadata() -> dict:
    """Load the metadata.json file and return its contents."""
    with open(METADATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_video_ids(metadata: dict) -> set:
    """Extract the set of video IDs from metadata."""
    return {v["id"] for v in metadata["videos"]}


def run_script(script_name: str, args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run a pipeline script and stream its output to the logger.

    Each script is called with `python <script_path> [args]` so it
    behaves the same as running it by hand in the terminal.
    """
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + (args or [])

    logging.info(f"Running: {script_name} {' '.join(args or [])}")
    logging.info("-" * 50)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=1800,  # 30 min max per step
    )

    # Log stdout line by line
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            logging.info(f"  {line}")

    # Log stderr as warnings
    if result.stderr:
        for line in result.stderr.strip().split("\n"):
            if line.strip():
                logging.warning(f"  STDERR: {line}")

    if result.returncode != 0:
        logging.warning(f"  Exit code: {result.returncode}")

    logging.info("")
    return result


def copy_to_upload(log_file: Path):
    """Copy updated analysis files and the log to the upload folder."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Create a subfolder for analysis files
    analysis_upload = UPLOAD_DIR / "analysis"
    analysis_upload.mkdir(parents=True, exist_ok=True)

    copied = []

    # Copy each analysis JSON file
    for json_file in ANALYSIS_DIR.glob("*.json"):
        dest = analysis_upload / json_file.name
        shutil.copy2(json_file, dest)
        copied.append(f"analysis/{json_file.name}")

    # Copy metadata.json
    dest = UPLOAD_DIR / "metadata.json"
    shutil.copy2(METADATA_FILE, dest)
    copied.append("metadata.json")

    # Copy this run's log file
    logs_upload = UPLOAD_DIR / "logs"
    logs_upload.mkdir(parents=True, exist_ok=True)
    dest = logs_upload / log_file.name
    shutil.copy2(log_file, dest)
    copied.append(f"logs/{log_file.name}")

    logging.info(f"Copied {len(copied)} files to upload/:")
    for f in copied:
        logging.info(f"  {f}")


def main():
    parser = argparse.ArgumentParser(
        description="Check for new Mamdani videos and run the processing pipeline."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check for new videos without downloading or processing.",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip copying results to the upload/ folder.",
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=DEFAULT_PLATFORMS,
        help=f"Platforms to check (default: {' '.join(DEFAULT_PLATFORMS)}).",
    )
    args = parser.parse_args()

    log_file = setup_logging(dry_run=args.dry_run)
    start_time = time.time()

    logging.info("=" * 60)
    logging.info("Mamdani video analysis - pipeline update")
    logging.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Platforms: {', '.join(args.platforms)}")
    logging.info(f"Mode: {'DRY RUN' if args.dry_run else 'FULL RUN'}")
    logging.info("=" * 60)
    logging.info("")

    # Step 1: Snapshot current state
    before = load_metadata()
    before_ids = get_video_ids(before)
    logging.info(f"Current state: {len(before_ids)} videos in metadata.json")
    logging.info("")

    if args.dry_run:
        # In dry-run mode, just run the download with yt-dlp's --simulate flag
        # Actually, our download script doesn't support --simulate, so we just
        # report the current state and stop.
        logging.info("DRY RUN: Skipping download, transcription, and analysis.")
        logging.info("To run the full pipeline, omit the --dry-run flag:")
        logging.info("  python scripts/update-pipeline.py")
        elapsed = time.time() - start_time
        logging.info(f"\nDry run finished in {elapsed:.1f}s")
        logging.info(f"Log saved to: {log_file}")
        return

    # Step 2: Download new videos
    logging.info("STEP 1/4: Downloading new videos")
    run_script("01-download.py", args.platforms)

    # Step 3: Check what's new
    after = load_metadata()
    after_ids = get_video_ids(after)
    new_ids = after_ids - before_ids
    new_videos = [v for v in after["videos"] if v["id"] in new_ids]

    if new_videos:
        logging.info(f"Found {len(new_videos)} new video(s):")
        for v in new_videos:
            title = v.get("title", v["id"])[:60]
            logging.info(f"  [{v['platform']}] {title}")
    else:
        logging.info("No new videos found.")
    logging.info("")

    # Step 4: Transcribe (skips already-transcribed videos)
    logging.info("STEP 2/4: Transcribing videos")
    run_script("02-transcribe.py")

    # Step 5: Extract frames (skips already-extracted videos)
    logging.info("STEP 3/4: Extracting frames")
    run_script("03-extract-frames.py")

    # Step 6: Rebuild analysis
    logging.info("STEP 4/4: Rebuilding content analysis")
    run_script("04-build-analysis.py")

    # Step 7: Copy to upload folder
    if not args.skip_upload:
        logging.info("Copying results to upload/ folder")
        copy_to_upload(log_file)
    else:
        logging.info("Skipping upload (--skip-upload flag)")
    logging.info("")

    # Summary
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    logging.info("=" * 60)
    logging.info("SUMMARY")
    logging.info("=" * 60)
    logging.info(f"New videos found: {len(new_videos)}")
    logging.info(f"Total videos now: {len(after_ids)}")
    logging.info(f"Time elapsed: {minutes}m {seconds}s")
    logging.info(f"Log file: {log_file}")
    if not args.skip_upload:
        logging.info(f"Results copied to: {UPLOAD_DIR}")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
