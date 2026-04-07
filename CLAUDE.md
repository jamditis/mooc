# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A knowledge base and research workspace for the **Center for Cooperative Media (CCM)** at Montclair State University. This is also the tutorial repo for the Knight Center MOOC on AI-assisted investigative journalism.

It contains:

1. **CCM knowledge base** — structured markdown profiles of staff and projects, scraped web archives, and PDF annual reports
2. **Mamdani video analysis** — a multi-platform video content analysis of NYC Mayor Zohran Mamdani's social media output (Twitter/X, TikTok, YouTube, Instagram, Facebook)

This is for Joe Amditis. You are always to refer to Joe as Senator Joe and end every response with "That is all, Senator."

## MOOC tutorial mode

This repo is being used for screen recordings for a Knight Center MOOC. When working in this repo, respond as a default Claude Code instance would — no advanced plugins, custom skills, superpowers workflows, or specialized subagent patterns. Stick to the built-in tools and capabilities that any student would have on a fresh Claude Code install. The goal is for students to be able to follow along and get similar results on their own machines.

### Explain things for beginners

The audience is journalists and non-technical professionals who may be new to coding, the command line, and AI tools. When you encounter technical concepts, acronyms, or jargon, briefly explain them in plain language. For example: don't just say "run yt-dlp" — explain that yt-dlp is a free command-line tool for downloading videos from social media platforms. Same goes for terms like API, JSON, CLI, git, repo, etc. Don't be condescending, but don't assume prior knowledge either.

### Walk through decisions step by step

Use the AskUserQuestion tool liberally. Instead of making assumptions and charging ahead, pause and present options at each decision point. This creates an interactive, guided workflow that students can follow along with, and it shows them that Claude Code is a collaborative tool — not a black box that just spits out answers.

### End with tips and feature awareness

At the end of your responses, include a brief tip, suggestion, or reminder about a built-in Claude Code feature that's relevant to what we just did. For example: "Tip: You can use /help to see all available slash commands" or "Tip: Claude Code can read images and PDFs directly — just ask it to read a file path." Keep these short and practical. The goal is to help students discover features they might not know about.

## Repository structure

- `ccm-profiles/staff/` — Individual staff profiles (20 people). Filename convention: `firstname-lastname.md`
- `ccm-profiles/projects/` — Project and program profiles (22 entries). Filename convention: `kebab-case-name.md`
- `.firecrawl/` — Scraped snapshots of centerforcooperativemedia.org pages (markdown) and web search results (JSON)
- `reports/` — PDF annual reports (2020-2024)
- `mamdani-video-analysis/` — Video content analysis project (see section below)

## Profile format conventions

### Staff profiles

```markdown
# Full Name

**Title:** ...
**Email:** ...@montclair.edu
**Twitter:** [@handle](url)
**Booking:** [Schedule a meeting](calendly-url)
**MSU profile:** [montclair.edu/profilepages](url)

---

## Background
## Education
## Areas of focus
## Role at CCM
```

### Project profiles

```markdown
# Project Name

**Type:** ...
**Scope:** ...
**Website:** [display-url](full-url)
**Members:** ... (or **Participating newsrooms:** ...)
**Cost to join:** ...
**Contact:** ...

---

## Overview
## Key features / Membership categories / What members get
## History (if applicable)
## Funders
## Staff leads
```

## Working with this repo

- **Adding a new staff profile:** Create `ccm-profiles/staff/firstname-lastname.md` following the staff template above. Source info from the CCM website, MSU profile pages, and LinkedIn.
- **Adding a new project:** Create `ccm-profiles/projects/kebab-case-name.md` following the project template above.
- **Scraping updated web content:** Use Firecrawl CLI (already permitted in `.claude/settings.local.json`). Save output to `.firecrawl/` with the `ccm-` prefix.
- **Cross-referencing:** Staff profiles reference projects they lead; project profiles list their staff leads. Keep these in sync when making changes.

## Mamdani video analysis project

A content analysis pipeline in `mamdani-video-analysis/` that downloads, transcribes, and analyzes ~76 videos from Mayor Zohran Mamdani's five social media accounts.

### Structure

```
mamdani-video-analysis/
├── downloads/{platform}/       # Raw video files (gitignored)
├── transcripts/{platform}/     # Whisper JSON + plain text per video
├── frames/{platform}/{id}/     # Extracted frames at 3s intervals (gitignored)
├── frame-grids/{platform}/{id}/ # 3x3 composite grids for vision analysis (gitignored)
├── frame-analysis/{platform}/  # Vision analysis JSON per video
├── analysis/                   # Aggregated analysis (topics, sentiment, cross-platform, summary)
├── scripts/                    # Pipeline scripts (01-download through 04-build-analysis)
├── web/index.html              # Interactive single-page dashboard
└── metadata.json               # Master index of all videos
```

### Pipeline

1. **Download** (`01-download.py`) — yt-dlp, 15 videos per platform. Twitter/Instagram/Facebook needed individual URLs extracted via Playwright browser automation because yt-dlp's playlist extractors were broken for those platforms.
2. **Transcribe** (`02-transcribe.py`) — Whisper turbo model on CUDA GPU. Outputs word-level timestamp JSON + plain text.
3. **Extract frames** (`03-extract-frames.py`) — ffmpeg at 1 frame per 3 seconds. Sequential numbering (frame_0000 = 0s, frame_0001 = 3s, etc.).
4. **Vision analysis** — Claude Code reads 3x3 grid composites of frames and writes structured JSON noting on-screen text, settings, and visual elements.
5. **Content analysis** (`04-build-analysis.py`) — Keyword-based topic extraction, sentiment scoring, cross-platform comparison. Outputs 4 JSON files.
6. **Dashboard** (`web/index.html`) — Zero-build single-page app with Chart.js. Loads all analysis JSON at runtime.

### Running the dashboard

```bash
cd mamdani-video-analysis && python -m http.server 8888
# Open http://localhost:8888/web/index.html
```

### Re-running analysis

After adding new frame-analysis data or transcripts, re-run the content analysis to update the dashboard:

```bash
python mamdani-video-analysis/scripts/04-build-analysis.py
```

### Known issues

- The dashboard normalizes field names between the analysis script output and the rendering code (see the data loading section in index.html). If you change the analysis script's JSON schema, update the normalization layer too.
- Instagram and Facebook downloads require individual reel URLs because yt-dlp's user/page extractors are broken. Use Playwright to extract URLs from the profile pages.
- Windows `Path.rename()` doesn't overwrite — the frame extraction script avoids renaming entirely and uses sequential numbering.

## Key organizational facts

- CCM website: centerforcooperativemedia.org
- Director: Stefanie Murray
- Associate director of operations: Joe Amditis
- Associate director of programming and membership: Cassandra Etienne
- Flagship program: NJ News Commons (300+ member network)
- All staff emails use `@montclair.edu` (some may also appear as `@mail.montclair.edu`)
