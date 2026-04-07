# Mamdani video analysis implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Download, transcribe, and analyze ~75 videos from Mayor Zohran Mamdani's five social media accounts, then present findings in an interactive dashboard.

**Architecture:** Sequential pipeline — download all videos, then batch transcribe with GPU-accelerated Whisper, extract frames at 3-second intervals, analyze frames with Claude Code vision, aggregate into content analysis JSONs, and serve via a zero-build single-page dashboard.

**Tech Stack:** yt-dlp (download), openai-whisper large-v3 + CUDA (transcription), ffmpeg (frames), Claude Code Read tool (vision/OCR), Chart.js + vanilla JS (dashboard)

---

## File map

| File | Responsibility |
|------|---------------|
| `mamdani-video-analysis/.gitignore` | Exclude downloads/ and frames/ from git |
| `mamdani-video-analysis/scripts/01-download.py` | yt-dlp wrapper: downloads 15 videos per platform, writes metadata.json |
| `mamdani-video-analysis/scripts/02-transcribe.py` | Whisper wrapper: transcribes all downloaded videos, outputs JSON + TXT |
| `mamdani-video-analysis/scripts/03-extract-frames.py` | ffmpeg wrapper: extracts frames at 3s intervals from all videos |
| `mamdani-video-analysis/scripts/04-build-analysis.py` | Reads transcripts + frame-analysis, produces aggregated analysis JSONs |
| `mamdani-video-analysis/metadata.json` | Master index of all videos with IDs, titles, dates, durations, URLs |
| `mamdani-video-analysis/web/index.html` | Single-page interactive dashboard |

---

### Task 1: Fix Whisper dependency and scaffold project

**Files:**
- Create: `mamdani-video-analysis/.gitignore`
- Create: `mamdani-video-analysis/metadata.json`
- Create: `mamdani-video-analysis/scripts/` (empty dir structure)

- [ ] **Step 1: Fix NumPy version for Whisper**

Whisper's numba dependency requires NumPy <= 2.3. Current version is 2.4.4.

```bash
pip install "numpy<2.4"
```

Verify fix:
```bash
python -c "import whisper; print('Whisper OK')"
```

Expected: `Whisper OK`

- [ ] **Step 2: Create project directory structure**

```bash
cd C:/Users/amdit/OneDrive/Desktop/mooc
mkdir -p mamdani-video-analysis/{downloads/{twitter,tiktok,youtube,instagram,facebook},transcripts/{twitter,tiktok,youtube,instagram,facebook},frames/{twitter,tiktok,youtube,instagram,facebook},frame-analysis,analysis,scripts,web}
```

- [ ] **Step 3: Create .gitignore for the project subfolder**

Write `mamdani-video-analysis/.gitignore`:

```gitignore
# Video files are too large for git
downloads/
frames/

# OS files
desktop.ini
Thumbs.db
```

- [ ] **Step 4: Create empty metadata.json**

Write `mamdani-video-analysis/metadata.json`:

```json
{
  "project": "mamdani-video-analysis",
  "created": "2026-04-01",
  "sources": {
    "twitter": "https://twitter.com/ZohranKMamdani/media",
    "tiktok": "https://www.tiktok.com/@zohran_k_mamdani",
    "youtube": "https://www.youtube.com/@ZohranforNYC",
    "instagram": "https://www.instagram.com/nycmayor/",
    "facebook": "https://www.facebook.com/NYCMayor/reels/"
  },
  "videos": []
}
```

- [ ] **Step 5: Commit scaffold**

```bash
git add mamdani-video-analysis/.gitignore mamdani-video-analysis/metadata.json
git commit -m "Scaffold mamdani-video-analysis project structure"
```

---

### Task 2: Write and run the download script

**Files:**
- Create: `mamdani-video-analysis/scripts/01-download.py`
- Modify: `mamdani-video-analysis/metadata.json`

- [ ] **Step 1: Write the download script**

Write `mamdani-video-analysis/scripts/01-download.py`:

```python
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

    # Use yt-dlp to download and dump metadata JSON
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
            timeout=600,  # 10 min per platform
        )

        # yt-dlp --print-json outputs one JSON object per line per video
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                info = json.loads(line)
                video_file = out_dir / f"{info['id']}.mp4"
                if not video_file.exists():
                    # Try other extensions
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
                print(f"  OK: {info.get('title', info.get('id', '?'))[:60]}")
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

        if result.returncode != 0 and not videos:
            print(f"  WARN: yt-dlp exited {result.returncode}")
            if result.stderr:
                # Print last 5 lines of stderr for debugging
                for line in result.stderr.strip().split("\n")[-5:]:
                    print(f"  stderr: {line}")

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
    # Allow running for specific platforms: python 01-download.py youtube twitter
    platforms = sys.argv[1:] if len(sys.argv) > 1 else list(SOURCES.keys())

    # Load existing metadata
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

    # Sort by upload date descending
    metadata["videos"].sort(key=lambda v: v["upload_date"], reverse=True)

    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    total = len(metadata["videos"])
    print(f"\nDone. {total} total videos in metadata.json")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the download script — start with YouTube (most reliable)**

```bash
cd C:/Users/amdit/OneDrive/Desktop/mooc
python mamdani-video-analysis/scripts/01-download.py youtube
```

Expected: 15 videos downloaded to `mamdani-video-analysis/downloads/youtube/`, metadata.json updated.

Verify:
```bash
ls mamdani-video-analysis/downloads/youtube/*.mp4 | wc -l
python -c "import json; d=json.load(open('mamdani-video-analysis/metadata.json')); print(f'{len(d[\"videos\"])} videos')"
```

- [ ] **Step 3: Run for Twitter**

```bash
python mamdani-video-analysis/scripts/01-download.py twitter
```

If Twitter requires auth, export cookies from Chrome:
```bash
yt-dlp --cookies-from-browser chrome --playlist-items 1:1 --simulate "https://twitter.com/ZohranKMamdani/media"
```

If that works, update the script to add `--cookies-from-browser chrome` for twitter.

- [ ] **Step 4: Run for TikTok**

```bash
python mamdani-video-analysis/scripts/01-download.py tiktok
```

TikTok may need cookies. If it fails, try:
```bash
yt-dlp --cookies-from-browser chrome --playlist-items 1:1 --simulate "https://www.tiktok.com/@zohran_k_mamdani"
```

- [ ] **Step 5: Run for Instagram**

Note: `instagram:user` extractor is currently broken in yt-dlp. Try first:
```bash
python mamdani-video-analysis/scripts/01-download.py instagram
```

If this fails, fall back to:
1. Use `--cookies-from-browser chrome` with Instagram
2. Or use Playwright to get individual reel URLs, then download each one separately with yt-dlp
3. Or manually collect 15 reel URLs from the browser and feed them to yt-dlp one by one

- [ ] **Step 6: Run for Facebook**

```bash
python mamdani-video-analysis/scripts/01-download.py facebook
```

Facebook reels may need cookies:
```bash
yt-dlp --cookies-from-browser chrome --playlist-items 1:1 --simulate "https://www.facebook.com/NYCMayor/reels/"
```

- [ ] **Step 7: Verify all downloads and commit script + metadata**

```bash
python -c "
import json
d = json.load(open('mamdani-video-analysis/metadata.json'))
from collections import Counter
counts = Counter(v['platform'] for v in d['videos'])
for p, c in sorted(counts.items()):
    print(f'  {p}: {c} videos')
print(f'  Total: {len(d[\"videos\"])} videos')
"
```

```bash
git add mamdani-video-analysis/scripts/01-download.py mamdani-video-analysis/metadata.json
git commit -m "Add download script and video metadata for Mamdani analysis"
```

---

### Task 3: Write and run the transcription script

**Files:**
- Create: `mamdani-video-analysis/scripts/02-transcribe.py`
- Create: `mamdani-video-analysis/transcripts/{platform}/{video-id}.json` (output)
- Create: `mamdani-video-analysis/transcripts/{platform}/{video-id}.txt` (output)

- [ ] **Step 1: Verify Whisper works on GPU**

```bash
python -c "
import whisper
import torch
print(f'CUDA: {torch.cuda.is_available()}')
model = whisper.load_model('large-v3', device='cuda')
print('Model loaded OK')
del model
torch.cuda.empty_cache()
"
```

Expected: `CUDA: True` and `Model loaded OK`

- [ ] **Step 2: Write the transcription script**

Write `mamdani-video-analysis/scripts/02-transcribe.py`:

```python
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

    # Skip if already transcribed
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

        # Save full JSON with word-level timestamps
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        # Save plain text
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

    # Optional: filter by platform
    platforms_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    videos = metadata["videos"]
    if platforms_filter:
        videos = [v for v in videos if v["platform"] in platforms_filter]

    print(f"Loading Whisper large-v3 on CUDA...")
    model = whisper.load_model("large-v3", device="cuda")
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

    # Free GPU memory
    del model
    torch.cuda.empty_cache()

    print(f"\nDone. {success} transcribed, {failed} failed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run transcription**

```bash
cd C:/Users/amdit/OneDrive/Desktop/mooc
python mamdani-video-analysis/scripts/02-transcribe.py
```

This will take a while — roughly 1-3 minutes per video depending on length. Monitor GPU usage:
```bash
nvidia-smi
```

- [ ] **Step 4: Verify transcripts and commit**

```bash
find mamdani-video-analysis/transcripts -name "*.txt" | wc -l
# Spot-check a transcript:
head -c 500 mamdani-video-analysis/transcripts/youtube/*.txt | head -20
```

```bash
git add mamdani-video-analysis/scripts/02-transcribe.py mamdani-video-analysis/transcripts/
git commit -m "Add transcription script and Whisper transcripts"
```

---

### Task 4: Write and run the frame extraction script

**Files:**
- Create: `mamdani-video-analysis/scripts/03-extract-frames.py`
- Create: `mamdani-video-analysis/frames/{platform}/{video-id}/frame_NNNN.jpg` (output, gitignored)

- [ ] **Step 1: Write the frame extraction script**

Write `mamdani-video-analysis/scripts/03-extract-frames.py`:

```python
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

    # Skip if already extracted (check for at least one frame)
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
        "-q:v", "2",  # JPEG quality (2 = ~95%)
        "-start_number", "0",
        str(out_dir / "frame_%04d.jpg"),
        "-y",  # Overwrite
        "-loglevel", "error",
    ]

    try:
        subprocess.run(cmd, check=True, timeout=120)
        frames = list(out_dir.glob("frame_*.jpg"))

        # Rename frames to use seconds instead of sequence numbers
        # frame_0000.jpg -> frame_0000.jpg (0s), frame_0001.jpg -> frame_0003.jpg (3s), etc.
        for frame in sorted(frames):
            seq = int(frame.stem.split("_")[1])
            seconds = seq * 3
            new_name = out_dir / f"frame_{seconds:04d}.jpg"
            if frame != new_name:
                frame.rename(new_name)

        final_frames = list(out_dir.glob("frame_*.jpg"))
        print(f"  OK: {len(final_frames)} frames from {video_id}")
        return len(final_frames)

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
```

- [ ] **Step 2: Run frame extraction**

```bash
cd C:/Users/amdit/OneDrive/Desktop/mooc
python mamdani-video-analysis/scripts/03-extract-frames.py
```

This is fast — ffmpeg handles it in seconds per video.

- [ ] **Step 3: Verify frame counts and commit**

```bash
# Count total frames
find mamdani-video-analysis/frames -name "*.jpg" | wc -l

# Spot-check a video's frames
ls mamdani-video-analysis/frames/youtube/ | head -3
```

```bash
git add mamdani-video-analysis/scripts/03-extract-frames.py
git commit -m "Add frame extraction script (3-second intervals)"
```

---

### Task 5: Vision analysis of frames (interactive)

**Files:**
- Create: `mamdani-video-analysis/frame-analysis/{platform}/{video-id}.json` (per video)

This task is interactive. The implementer (Claude Code) reads frames using the Read tool and writes structured analysis JSON.

- [ ] **Step 1: Create a helper script to list frames needing analysis**

Write a quick frame inventory to know what to analyze:

```bash
cd C:/Users/amdit/OneDrive/Desktop/mooc
python -c "
import json
from pathlib import Path

base = Path('mamdani-video-analysis')
metadata = json.load(open(base / 'metadata.json'))
frames_dir = base / 'frames'
analysis_dir = base / 'frame-analysis'

for video in metadata['videos']:
    vid_id = video['id']
    platform = video['platform']
    frame_dir = frames_dir / platform / vid_id
    analysis_file = analysis_dir / platform / f'{vid_id}.json'

    frames = sorted(frame_dir.glob('frame_*.jpg')) if frame_dir.exists() else []
    done = analysis_file.exists()
    status = 'DONE' if done else f'{len(frames)} frames'
    print(f'  {platform}/{vid_id}: {status}')
"
```

- [ ] **Step 2: For each video, read frames in batches and write analysis**

For each video that has frames but no analysis file:

1. Read 5-10 frames at a time using the Read tool (Claude Code can view images)
2. For each frame, note:
   - Any on-screen text (captions, headlines, lower-thirds, graphics, watermarks)
   - Visual setting (office, street, studio, etc.)
   - Key visual elements (charts, photos, people visible)
   - Presentation style (formal/casual, graphics overlay, etc.)
3. Write results to `frame-analysis/{platform}/{video-id}.json`:

```json
{
  "video_id": "abc123",
  "platform": "youtube",
  "frames": [
    {
      "timestamp_seconds": 0,
      "file": "frame_0000.jpg",
      "on_screen_text": ["Mayor's Office", "Live from City Hall"],
      "setting": "City Hall press room",
      "visual_elements": ["podium", "NYC seal", "microphones"],
      "presentation_style": "formal press conference"
    }
  ],
  "summary": {
    "dominant_setting": "City Hall press room",
    "text_overlay_types": ["lower-third captions", "topic headers"],
    "visual_themes": ["formal governance"]
  }
}
```

- [ ] **Step 3: Commit frame analysis as batches are completed**

```bash
git add mamdani-video-analysis/frame-analysis/
git commit -m "Add frame analysis for [platform] videos"
```

Repeat for each platform batch.

---

### Task 6: Write and run the content analysis script

**Files:**
- Create: `mamdani-video-analysis/scripts/04-build-analysis.py`
- Create: `mamdani-video-analysis/analysis/topics.json`
- Create: `mamdani-video-analysis/analysis/sentiment.json`
- Create: `mamdani-video-analysis/analysis/cross-platform.json`
- Create: `mamdani-video-analysis/analysis/summary.json`

- [ ] **Step 1: Write the content analysis script**

Write `mamdani-video-analysis/scripts/04-build-analysis.py`:

```python
"""Build aggregated content analysis from transcripts and frame analysis."""

import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METADATA_FILE = BASE_DIR / "metadata.json"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
FRAME_ANALYSIS_DIR = BASE_DIR / "frame-analysis"
ANALYSIS_DIR = BASE_DIR / "analysis"

# Topic keywords — tuned for NYC mayoral content
TOPIC_KEYWORDS = {
    "housing": ["housing", "rent", "tenant", "landlord", "eviction", "affordable", "apartment", "shelter", "homeless"],
    "transit": ["subway", "mta", "bus", "transit", "commute", "train", "transportation", "congestion"],
    "public_safety": ["crime", "police", "nypd", "safety", "gun", "violence", "shooting", "officer"],
    "education": ["school", "student", "teacher", "education", "class", "college", "university"],
    "economy": ["job", "business", "economy", "wage", "worker", "employment", "union", "labor"],
    "health": ["health", "hospital", "mental health", "covid", "vaccine", "doctor", "care"],
    "immigration": ["immigrant", "migrant", "asylum", "deportation", "border", "ice"],
    "environment": ["climate", "green", "park", "pollution", "clean energy", "sustainability"],
    "budget": ["budget", "tax", "spending", "funding", "fiscal", "billion", "million"],
    "governance": ["city council", "legislation", "bill", "executive order", "policy", "administration"],
}

SENTIMENT_WORDS = {
    "positive": ["proud", "progress", "success", "achieve", "celebrate", "improve", "opportunity", "together", "forward", "invest", "build", "protect", "deliver", "win"],
    "negative": ["crisis", "fail", "broken", "wrong", "problem", "suffer", "struggle", "fight", "attack", "cut", "loss", "threat", "danger", "oppose"],
    "urgent": ["now", "immediately", "must", "emergency", "critical", "urgent", "demand", "action", "cannot wait"],
}


def load_transcripts() -> dict[str, dict]:
    """Load all transcripts keyed by video ID."""
    transcripts = {}
    for txt_file in TRANSCRIPTS_DIR.rglob("*.txt"):
        video_id = txt_file.stem
        platform = txt_file.parent.name
        text = txt_file.read_text(encoding="utf-8").strip()
        transcripts[video_id] = {
            "platform": platform,
            "text": text,
            "words": text.lower().split(),
            "word_count": len(text.split()),
        }
    return transcripts


def load_frame_analyses() -> dict[str, dict]:
    """Load all frame analysis JSONs keyed by video ID."""
    analyses = {}
    for json_file in FRAME_ANALYSIS_DIR.rglob("*.json"):
        video_id = json_file.stem
        with open(json_file, encoding="utf-8") as f:
            analyses[video_id] = json.load(f)
    return analyses


def analyze_topics(transcripts: dict, metadata: dict) -> dict:
    """Extract topic frequency from transcripts."""
    per_video = {}
    per_platform = {}
    overall = Counter()

    for video in metadata["videos"]:
        vid_id = video["id"]
        platform = video["platform"]
        if vid_id not in transcripts:
            continue

        text_lower = transcripts[vid_id]["text"].lower()
        video_topics = {}

        for topic, keywords in TOPIC_KEYWORDS.items():
            count = sum(text_lower.count(kw) for kw in keywords)
            if count > 0:
                video_topics[topic] = count
                overall[topic] += count
                if platform not in per_platform:
                    per_platform[platform] = Counter()
                per_platform[platform][topic] += count

        per_video[vid_id] = {
            "title": video.get("title", ""),
            "platform": platform,
            "topics": video_topics,
        }

    return {
        "overall": dict(overall.most_common()),
        "per_platform": {p: dict(c.most_common()) for p, c in per_platform.items()},
        "per_video": per_video,
    }


def analyze_sentiment(transcripts: dict, metadata: dict) -> dict:
    """Classify sentiment/tone per video."""
    results = {}

    for video in metadata["videos"]:
        vid_id = video["id"]
        if vid_id not in transcripts:
            continue

        text_lower = transcripts[vid_id]["text"].lower()
        scores = {}
        for sentiment, words in SENTIMENT_WORDS.items():
            scores[sentiment] = sum(text_lower.count(w) for w in words)

        total = sum(scores.values()) or 1
        normalized = {k: round(v / total, 3) for k, v in scores.items()}

        # Determine dominant tone
        dominant = max(scores, key=scores.get) if any(scores.values()) else "neutral"

        results[vid_id] = {
            "title": video.get("title", ""),
            "platform": video["platform"],
            "raw_counts": scores,
            "normalized": normalized,
            "dominant_tone": dominant,
            "word_count": transcripts[vid_id]["word_count"],
        }

    # Aggregate by platform
    platform_agg = {}
    for vid_id, data in results.items():
        p = data["platform"]
        if p not in platform_agg:
            platform_agg[p] = {"positive": 0, "negative": 0, "urgent": 0, "count": 0}
        for tone in ["positive", "negative", "urgent"]:
            platform_agg[p][tone] += data["raw_counts"].get(tone, 0)
        platform_agg[p]["count"] += 1

    return {
        "per_video": results,
        "per_platform": platform_agg,
    }


def analyze_cross_platform(transcripts: dict, frame_analyses: dict, metadata: dict) -> dict:
    """Compare messaging across platforms."""
    platform_data = {}

    for video in metadata["videos"]:
        vid_id = video["id"]
        platform = video["platform"]
        if platform not in platform_data:
            platform_data[platform] = {
                "video_count": 0,
                "total_words": 0,
                "total_duration": 0,
                "all_text": [],
                "on_screen_text": [],
                "settings": [],
            }

        platform_data[platform]["video_count"] += 1
        platform_data[platform]["total_duration"] += video.get("duration", 0)

        if vid_id in transcripts:
            platform_data[platform]["total_words"] += transcripts[vid_id]["word_count"]
            platform_data[platform]["all_text"].append(transcripts[vid_id]["text"])

        if vid_id in frame_analyses:
            fa = frame_analyses[vid_id]
            for frame in fa.get("frames", []):
                platform_data[platform]["on_screen_text"].extend(
                    frame.get("on_screen_text", [])
                )
                if frame.get("setting"):
                    platform_data[platform]["settings"].append(frame["setting"])

    # Build comparison
    comparison = {}
    for platform, data in platform_data.items():
        # Most common words (excluding stopwords)
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "shall", "can", "need", "dare", "ought",
                     "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
                     "and", "or", "but", "not", "no", "nor", "so", "yet", "both", "either",
                     "neither", "each", "every", "all", "any", "few", "more", "most", "other",
                     "some", "such", "than", "too", "very", "just", "because", "as", "until",
                     "while", "that", "this", "these", "those", "i", "you", "he", "she", "it",
                     "we", "they", "me", "him", "her", "us", "them", "my", "your", "his",
                     "its", "our", "their", "what", "which", "who", "whom", "when", "where",
                     "why", "how", "if", "then", "else", "about", "up", "out", "going",
                     "know", "think", "like", "really", "right", "well", "also", "get",
                     "got", "one", "two", "much", "many", "new", "way", "make", "made"}

        combined_text = " ".join(data["all_text"]).lower()
        words = re.findall(r'\b[a-z]{3,}\b', combined_text)
        word_freq = Counter(w for w in words if w not in stopwords)

        setting_freq = Counter(data["settings"])

        comparison[platform] = {
            "video_count": data["video_count"],
            "total_words": data["total_words"],
            "total_duration_seconds": data["total_duration"],
            "avg_duration_seconds": round(data["total_duration"] / max(data["video_count"], 1)),
            "avg_words_per_video": round(data["total_words"] / max(data["video_count"], 1)),
            "top_words": dict(word_freq.most_common(20)),
            "on_screen_text_samples": data["on_screen_text"][:20],
            "common_settings": dict(setting_freq.most_common(5)),
        }

    return {
        "platforms": comparison,
        "platform_count": len(comparison),
        "total_videos": sum(c["video_count"] for c in comparison.values()),
    }


def build_summary(topics: dict, sentiment: dict, cross_platform: dict, metadata: dict) -> dict:
    """Build high-level summary."""
    total_videos = len(metadata["videos"])
    total_duration = sum(v.get("duration", 0) for v in metadata["videos"])
    platforms = list(set(v["platform"] for v in metadata["videos"]))

    top_topics = list(topics["overall"].keys())[:5]

    # Dominant tone across all videos
    tone_counts = Counter()
    for vid_data in sentiment.get("per_video", {}).values():
        tone_counts[vid_data["dominant_tone"]] += 1

    return {
        "total_videos": total_videos,
        "total_duration_seconds": total_duration,
        "total_duration_minutes": round(total_duration / 60, 1),
        "platforms": platforms,
        "platform_count": len(platforms),
        "top_topics": top_topics,
        "dominant_tone_distribution": dict(tone_counts),
        "videos_per_platform": dict(Counter(v["platform"] for v in metadata["videos"])),
    }


def main():
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    with open(METADATA_FILE) as f:
        metadata = json.load(f)

    print("Loading transcripts...")
    transcripts = load_transcripts()
    print(f"  Loaded {len(transcripts)} transcripts")

    print("Loading frame analyses...")
    frame_analyses = load_frame_analyses()
    print(f"  Loaded {len(frame_analyses)} frame analyses")

    print("Analyzing topics...")
    topics = analyze_topics(transcripts, metadata)
    with open(ANALYSIS_DIR / "topics.json", "w") as f:
        json.dump(topics, f, indent=2)

    print("Analyzing sentiment...")
    sentiment = analyze_sentiment(transcripts, metadata)
    with open(ANALYSIS_DIR / "sentiment.json", "w") as f:
        json.dump(sentiment, f, indent=2)

    print("Analyzing cross-platform patterns...")
    cross_platform = analyze_cross_platform(transcripts, frame_analyses, metadata)
    with open(ANALYSIS_DIR / "cross-platform.json", "w") as f:
        json.dump(cross_platform, f, indent=2)

    print("Building summary...")
    summary = build_summary(topics, sentiment, cross_platform, metadata)
    with open(ANALYSIS_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nDone. Analysis files written to {ANALYSIS_DIR}/")
    print(f"  Topics: {len(topics['overall'])} topics identified")
    print(f"  Videos analyzed: {summary['total_videos']}")
    print(f"  Total content: {summary['total_duration_minutes']} minutes")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the analysis script**

```bash
cd C:/Users/amdit/OneDrive/Desktop/mooc
python mamdani-video-analysis/scripts/04-build-analysis.py
```

- [ ] **Step 3: Verify outputs and commit**

```bash
python -c "
import json
for f in ['topics', 'sentiment', 'cross-platform', 'summary']:
    d = json.load(open(f'mamdani-video-analysis/analysis/{f}.json'))
    print(f'{f}.json: {len(json.dumps(d))} bytes')
"
```

```bash
git add mamdani-video-analysis/scripts/04-build-analysis.py mamdani-video-analysis/analysis/
git commit -m "Add content analysis script and results"
```

---

### Task 7: Build the interactive web dashboard

**Files:**
- Create: `mamdani-video-analysis/web/index.html`

- [ ] **Step 1: Build the single-page dashboard**

This is a large single-file HTML page. Use the `frontend-design` skill for the actual implementation. Key requirements:

- Zero-build: CDN-loaded Chart.js, vanilla JS, no bundler
- Inline SVG favicon
- Loads JSON data from `../analysis/` and `../metadata.json` and `../transcripts/` at runtime
- **Sections:**
  1. **Header** — project title, date range, total stats (videos, platforms, hours)
  2. **Video grid** — filterable by platform, each card shows title, platform badge, date, duration
  3. **Transcript search** — full-text search across all transcripts, shows matching excerpts with video context
  4. **Topic analysis** — bar chart of topic frequency, filterable by platform. Click a topic to see which videos mention it.
  5. **Sentiment visualization** — per-video sentiment breakdown (stacked bar or radar chart), platform-level aggregation
  6. **Cross-platform comparison** — side-by-side panels showing each platform's stats, top words, avg duration, content style
- Responsive layout, dark theme, distinctive design (not generic)
- All data loaded client-side from relative paths

The dashboard reads these files:
- `../metadata.json` — video list
- `../analysis/topics.json` — topic data
- `../analysis/sentiment.json` — sentiment data
- `../analysis/cross-platform.json` — platform comparison
- `../analysis/summary.json` — overview stats
- `../transcripts/{platform}/{id}.txt` — individual transcripts (loaded on demand)

- [ ] **Step 2: Test the dashboard locally**

```bash
cd C:/Users/amdit/OneDrive/Desktop/mooc/mamdani-video-analysis
python -m http.server 8888
```

Open `http://localhost:8888/web/index.html` in browser. Verify:
- All charts render
- Video grid populates
- Transcript search works
- Platform filters work
- Responsive on narrow viewport

- [ ] **Step 3: Commit the dashboard**

```bash
git add mamdani-video-analysis/web/index.html
git commit -m "Add interactive analysis dashboard"
```

---

### Task 8: Final verification and cleanup

- [ ] **Step 1: Run a full pipeline check**

```bash
cd C:/Users/amdit/OneDrive/Desktop/mooc
python -c "
import json
from pathlib import Path

base = Path('mamdani-video-analysis')
meta = json.load(open(base / 'metadata.json'))
videos = meta['videos']

print(f'Videos in metadata: {len(videos)}')

# Check downloads
downloaded = 0
for v in videos:
    if (base / v['local_path']).exists():
        downloaded += 1
print(f'Videos downloaded: {downloaded}')

# Check transcripts
transcribed = sum(1 for v in videos if (base / 'transcripts' / v['platform'] / f\"{v['id']}.txt\").exists())
print(f'Videos transcribed: {transcribed}')

# Check frames
framed = sum(1 for v in videos if (base / 'frames' / v['platform'] / v['id']).exists())
print(f'Videos with frames: {framed}')

# Check frame analysis
analyzed = sum(1 for v in videos if (base / 'frame-analysis' / v['platform'] / f\"{v['id']}.json\").exists())
print(f'Videos with frame analysis: {analyzed}')

# Check analysis outputs
for f in ['topics', 'sentiment', 'cross-platform', 'summary']:
    exists = (base / 'analysis' / f'{f}.json').exists()
    print(f'  {f}.json: {\"OK\" if exists else \"MISSING\"}')

print(f'Dashboard: {\"OK\" if (base / \"web\" / \"index.html\").exists() else \"MISSING\"}')
"
```

- [ ] **Step 2: Final commit with any remaining files**

```bash
git add mamdani-video-analysis/
git status
git commit -m "Complete Mamdani video analysis pipeline and dashboard"
```
