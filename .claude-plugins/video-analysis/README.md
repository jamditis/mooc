# video-analysis plugin

A Claude Code plugin for multi-platform social media video content analysis. Downloads videos, transcribes audio, extracts and analyzes frames, and builds interactive dashboards.

## Pipeline

Run the skills in order:

1. `/video-download` -- Download videos from Twitter/X, TikTok, YouTube, Instagram, Facebook
2. `/video-transcribe` -- Batch transcribe with Whisper (GPU-accelerated)
3. `/video-frames` -- Extract frames, create 3x3 grids, run vision analysis
4. `/video-dashboard` -- Generate topic/sentiment/cross-platform analysis + interactive dashboard

Each skill can also be used independently.

## System requirements

- **yt-dlp** -- `pip install yt-dlp`
- **ffmpeg** -- `choco install ffmpeg` (Windows) or `brew install ffmpeg` (macOS)
- **OpenAI Whisper** -- `pip install openai-whisper` (requires NumPy < 2.4)
- **Pillow** -- `pip install Pillow`
- **NVIDIA GPU** (recommended) -- CUDA-capable GPU with 6+ GB VRAM for fast transcription
- **Playwright** (optional) -- needed for Instagram/Facebook URL extraction fallback

## Quick start

```
/video-download
# Follow prompts: provide subject name and platform URLs
# Downloads 15 videos per platform

/video-transcribe
# Auto-detects GPU, runs Whisper turbo on all downloaded videos

/video-frames
# Extracts frames at 3-second intervals, creates grid composites, runs vision analysis

/video-dashboard
# Choose sections, generates analysis JSONs and interactive HTML dashboard
```

## Output structure

```
{subject}-video-analysis/
  downloads/{platform}/     # Video files (gitignored)
  transcripts/{platform}/   # Whisper JSON + text
  frames/{platform}/{id}/   # Extracted frames (gitignored)
  frame-grids/{platform}/   # 3x3 composites (gitignored)
  frame-analysis/{platform}/ # Vision analysis JSON
  analysis/                 # Topic, sentiment, cross-platform, summary
  web/index.html            # Interactive dashboard
  metadata.json             # Master video index
```
