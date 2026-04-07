# Mamdani video analysis — design spec

**Date:** 2026-04-01
**Purpose:** Content and text analysis of NYC Mayor Zohran Mamdani's social media video output across five platforms.
**Location:** `mooc/mamdani-video-analysis/`

---

## Goals

1. Download the 15 most recent videos from each of Mamdani's social media accounts (Twitter/X, TikTok, YouTube, Instagram, Facebook).
2. Transcribe all audio using Whisper large-v3 (GPU-accelerated).
3. Extract frames every 3 seconds for visual analysis.
4. Analyze frames using Claude Code's multimodal vision (Read tool) to catalog all on-screen text and visual messaging.
5. Run content analysis across all transcripts and frame data: topic/theme extraction, sentiment and tone, and cross-platform messaging comparison.
6. Build a single-page interactive web dashboard presenting the results.

## Source accounts

| Platform | URL | Target |
|----------|-----|--------|
| Twitter/X | https://twitter.com/ZohranKMamdani/media | 15 most recent videos |
| TikTok | https://www.tiktok.com/@zohran_k_mamdani | 15 most recent videos |
| YouTube | https://www.youtube.com/@ZohranforNYC | 15 most recent videos |
| Instagram | https://www.instagram.com/nycmayor/ | 15 most recent videos |
| Facebook | https://www.facebook.com/NYCMayor/reels/ | 15 most recent videos |

## Project structure

```
mooc/mamdani-video-analysis/
├── downloads/                    # Raw video files (gitignored)
│   ├── twitter/
│   ├── tiktok/
│   ├── youtube/
│   ├── instagram/
│   └── facebook/
├── transcripts/                  # Whisper output (JSON + plain text)
│   ├── twitter/
│   ├── tiktok/
│   ├── youtube/
│   ├── instagram/
│   └── facebook/
├── frames/                       # Extracted frames at 3s intervals (gitignored)
│   ├── twitter/{video-id}/
│   ├── tiktok/{video-id}/
│   ├── youtube/{video-id}/
│   ├── instagram/{video-id}/
│   └── facebook/{video-id}/
├── frame-analysis/               # Vision analysis results (JSON per video)
├── analysis/                     # Aggregated content analysis
│   ├── topics.json
│   ├── sentiment.json
│   ├── cross-platform.json
│   └── summary.json
├── scripts/                      # Pipeline automation
│   ├── 01-download.py
│   ├── 02-transcribe.py
│   ├── 03-extract-frames.py
│   └── 04-build-analysis.py
├── web/                          # Interactive dashboard
│   └── index.html
├── metadata.json                 # Master index of all videos
└── README.md
```

## Pipeline stages

### Stage 1: Download

- Tool: yt-dlp
- Downloads 15 most recent videos per platform
- Saves to `downloads/{platform}/` with yt-dlp's default naming (`{id}.{ext}`)
- Writes metadata to `metadata.json` with this schema per video:
  - `id`: yt-dlp extracted video ID
  - `title`: video title
  - `upload_date`: ISO 8601 date string
  - `duration`: seconds (integer)
  - `source_url`: original URL
  - `platform`: one of `twitter`, `tiktok`, `youtube`, `instagram`, `facebook`
  - `local_path`: relative path to downloaded file
  - `description`: video description if available
- Format preference: mp4 where available, best quality otherwise

### Stage 2: Transcribe

- Tool: openai-whisper, model `large-v3`, device `cuda`
- Input: all video files from `downloads/`
- Output per video:
  - `transcripts/{platform}/{video-id}.json` — word-level timestamps
  - `transcripts/{platform}/{video-id}.txt` — plain text transcript
- Processes videos sequentially (GPU memory management)

### Stage 3: Extract frames

- Tool: ffmpeg
- Rate: 1 frame every 3 seconds (`-vf fps=1/3`)
- Output: `frames/{platform}/{video-id}/frame_{seconds:04d}.jpg`
- Quality: JPEG at 95% quality, 1920px max width (scaled down if larger)

### Stage 4: Vision analysis

- Tool: Claude Code Read tool (multimodal vision)
- Process: read frames in batches, identify and catalog:
  - All on-screen text (captions, headlines, lower-thirds, graphics, watermarks)
  - Visual presentation style (setting, framing, graphics style)
  - Key visual elements
- Output: `frame-analysis/{platform}/{video-id}.json` with per-frame entries
- This stage is interactive and runs across Claude Code sessions

### Stage 5: Content analysis

- Aggregates transcripts + frame analysis data
- Produces:
  - `analysis/topics.json` — topic/theme extraction with frequency counts, per-platform breakdown
  - `analysis/sentiment.json` — sentiment and tone classification per video and aggregated
  - `analysis/cross-platform.json` — messaging differences across platforms, unique vs. shared content
  - `analysis/summary.json` — high-level findings

### Stage 6: Web dashboard

- Single HTML file at `web/index.html`
- Zero-build: CDN-loaded libraries (Chart.js or similar for charts, vanilla JS)
- Inline SVG favicon
- Sections:
  - Overview stats (total videos, platforms, hours of content)
  - Video grid with thumbnail, title, platform badge, date
  - Searchable transcript viewer
  - Topic frequency charts
  - Sentiment visualization
  - Cross-platform comparison panels
- Loads all analysis JSON files at runtime
- Responsive design, works offline once loaded

## Git strategy

- Video files (`downloads/`, `frames/`) added to `.gitignore` — too large for git
- Transcripts, analysis results, metadata, scripts, and web dashboard are committed
- Frame analysis JSON is committed (the analysis results, not the frames themselves)

## Technical constraints

- RTX 4080 Super with ~13GB free VRAM handles Whisper large-v3 comfortably
- yt-dlp supports all five platforms but some may require cookies for age-gated or login-walled content
- TikTok and Instagram can be flaky with yt-dlp; may need retries or browser cookie export
- Frame extraction at 3s intervals for 75 videos (avg 60s each) = ~1,500 frames total — manageable for interactive vision analysis across a few sessions

## Not in scope

- Real-time monitoring or scheduled re-scraping
- Comment/engagement analysis
- Audio analysis beyond transcription (music detection, etc.)
- Video re-hosting or redistribution
