# GEMINI.md

Instructional context for Gemini CLI in the **Center for Cooperative Media (CCM)** research workspace.

## Project overview

This repository is a combined knowledge base and research environment for the Center for Cooperative Media (CCM) at Montclair State University. It contains:

1.  **CCM knowledge base:** Structured profiles of staff and projects, scraped web archives, and references to annual reports.
2.  **Mamdani video analysis:** A multi-platform video content analysis pipeline focusing on NYC Mayor Zohran Mamdani's social media presence (Twitter/X, TikTok, YouTube, Instagram, Facebook).

## Architecture

### CCM knowledge base

- **Profiles:** Located in `ccm-profiles/`.
    - `staff/`: 20 individual staff profiles in Markdown format.
    - `projects/`: 22 project and program profiles in Markdown format.
- **Web archives:** Located in `.firecrawl/`. Contains Markdown snapshots and JSON search results from CCM-related web content.
- **Reports:** References to CCM annual reports (2020–2024) are documented in `reports/README.md`.

### Mamdani video analysis

A multi-stage Python pipeline located in `mamdani-video-analysis/`:

- **Data storage:**
    - `downloads/`: Raw video files (not tracked in Git).
    - `transcripts/`: Whisper-generated JSON and text transcripts.
    - `frames/` and `frame-grids/`: Extracted visual data for vision analysis (not tracked in Git).
    - `frame-analysis/`: Structured JSON from vision analysis.
- **Analysis results:** Located in `analysis/`. Contains aggregated JSON files for topics, sentiment, and cross-platform metrics.
- **Dashboard:** An interactive single-page app in `web/index.html` using Chart.js.

## Building and running

### Video analysis pipeline

The analysis follows a sequential numbered pipeline in `mamdani-video-analysis/scripts/`:

1.  **Download:** `python mamdani-video-analysis/scripts/01-download.py` (requires `yt-dlp`).
2.  **Transcribe:** `python mamdani-video-analysis/scripts/02-transcribe.py` (requires `openai-whisper` and `torch` with CUDA support).
3.  **Extract frames:** `python mamdani-video-analysis/scripts/03-extract-frames.py` (requires `ffmpeg`).
4.  **Analyze content:** `python mamdani-video-analysis/scripts/04-build-analysis.py` (aggregates transcripts and frame analysis into `analysis/`).
5.  **Batch analysis:** `python mamdani-video-analysis/scripts/05-batch-analysis.py` (for batch processing with external models).

### Running the dashboard

The results of the analysis can be viewed in a local web browser:

```bash
cd mamdani-video-analysis
python -m http.server 8888
# Open http://localhost:8888/web/index.html
```

### Dependencies (TODO)

There is currently no `requirements.txt` file. The environment requires:
- Python 3.x
- `yt-dlp`
- `ffmpeg`
- `torch` (CUDA-enabled)
- `openai-whisper`
- `playwright` (for browser automation tasks)

## Development conventions

### Profile templates

- **Staff profiles:** `ccm-profiles/staff/firstname-lastname.md`. Follow the template in `CLAUDE.md`.
- **Project profiles:** `ccm-profiles/projects/kebab-case-name.md`. Follow the template in `CLAUDE.md`.

### File naming

- **Scripts:** Use two-digit prefixes (e.g., `01-`, `02-`) for sequential pipeline scripts.
- **Web archives:** Use the `ccm-` prefix for files in `.firecrawl/`.

### Working with Claude

Consult `CLAUDE.md` for specific instructions related to Claude Code, including profile templates and project-specific trivia.
