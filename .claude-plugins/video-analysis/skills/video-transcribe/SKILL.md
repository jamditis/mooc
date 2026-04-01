---
name: video-transcribe
description: This skill should be used when the user asks to "transcribe videos", "transcribe audio", "run Whisper on videos", "generate transcripts", "extract text from video audio", or needs batch audio transcription of downloaded video files using OpenAI Whisper.
argument-hint: "[optional: path to video directory or metadata.json]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent", "AskUserQuestion"]
---

# Video transcription with Whisper

Batch transcribe video files using OpenAI Whisper with GPU acceleration. Produces word-level timestamp JSON and plain text transcripts for each video.

## Prerequisites

Verify before starting:

```bash
python -c "import whisper; print('Whisper OK')"
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

If Whisper fails to import, check for NumPy version conflicts:
- Whisper's numba dependency requires NumPy < 2.4
- Fix: `pip install "numpy<2.4"`

If CUDA is unavailable, Whisper will run on CPU (much slower but functional).

## Workflow

### Step 1: Auto-detect model

Check available GPU memory and select the appropriate model:

```bash
nvidia-smi --query-gpu=memory.free --format=csv,noheader 2>/dev/null
```

| Free VRAM | Model | Speed | Accuracy |
|-----------|-------|-------|----------|
| >= 6 GB | turbo | Fast (5-8x real-time) | Near-large quality |
| >= 3 GB | medium | Moderate | Good for clear speech |
| >= 1 GB | base | Moderate | Acceptable |
| No GPU | base (CPU) | Slow (0.5-1x real-time) | Acceptable |

**Default recommendation:** turbo. It handles clear English speech (interviews, press conferences, scripted videos) with near-large accuracy at 5-8x the speed.

Tell the user which model was selected and why. If they want to override, respect their choice.

### Step 2: Locate videos

Find the project's `metadata.json` or scan for video files:

```python
# From metadata.json
videos = metadata["videos"]  # has id, platform, local_path

# Or scan a directory
from pathlib import Path
videos = list(Path("downloads").rglob("*.mp4"))
```

### Step 3: Set up output directories

```bash
mkdir -p transcripts/{twitter,tiktok,youtube,instagram,facebook}
```

Output per video:
- `transcripts/{platform}/{video-id}.json` — full Whisper output with word-level timestamps
- `transcripts/{platform}/{video-id}.txt` — plain text transcript

### Step 4: Run transcription

Process videos sequentially to manage GPU memory. Skip already-transcribed files.

```python
import whisper
model = whisper.load_model("turbo", device="cuda")

result = model.transcribe(
    str(video_path),
    language="en",      # Set explicitly if known
    word_timestamps=True,
    verbose=False,
)
```

**For large batches:** Run platform by platform to avoid timeout issues. If a platform times out, re-run — the skip logic handles resumption.

**Progress reporting:** Print `[N/total] platform/title ... done (Xs, N words)` for each video.

### Step 5: Verify and report

Count transcripts per platform. Spot-check a few transcripts for quality. Report:
- Per-platform transcript counts
- Total words transcribed
- Any failures
- Time elapsed

Commit the transcription script and transcript files.

## Key lessons

- **Whisper turbo vs. large-v3:** For bulk English transcription, turbo is the right default. large-v3 takes 3-5x longer with marginal accuracy improvement on clear speech. Reserve large-v3 for noisy audio, accented speech, or multilingual content.
- **GPU memory:** Whisper large-v3 uses ~3GB VRAM, turbo ~6GB. Monitor with `nvidia-smi`. If VRAM is tight, use medium.
- **NumPy version:** Whisper's numba dependency breaks with NumPy >= 2.4. Always check this first.
- **Resume-safe:** Design scripts to skip already-transcribed files so re-runs are safe.
- **Audio extraction not needed:** Whisper handles video files directly via internal ffmpeg. Pre-extracting audio saves minimal time.

## Reference scripts

The template transcription script is at: `${CLAUDE_PLUGIN_ROOT}/scripts/transcribe-videos.py`
