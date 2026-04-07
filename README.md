# mooc

Knowledge base and research workspace for the [Center for Cooperative Media](https://centerforcooperativemedia.org/) (CCM) at Montclair State University.

Contains CCM staff and program profiles, scraped web archives, annual report references, and a multi-platform video content analysis of NYC Mayor Zohran Mamdani's social media.

## What's in here

```
mooc/
├── ccm-profiles/
│   ├── staff/                  # 20 staff profiles
│   └── projects/               # 22 project/program profiles
├── mamdani-video-analysis/
│   ├── downloads/              # 76 videos from 5 platforms (gitignored)
│   ├── transcripts/            # Whisper transcripts (JSON + text)
│   ├── frames/                 # Extracted frames at 3s intervals (gitignored)
│   ├── frame-analysis/         # Vision analysis of on-screen text and visuals
│   ├── analysis/               # Topic, sentiment, and cross-platform analysis
│   ├── scripts/                # Pipeline automation (download, transcribe, extract, analyze)
│   ├── web/                    # Interactive dashboard
│   └── metadata.json           # Master video index
├── .firecrawl/                 # 13 scraped web snapshots (markdown + JSON)
├── reports/                    # Annual reports (PDFs not tracked -- see reports/README.md)
├── CLAUDE.md                   # Claude Code project instructions
├── CONTRIBUTING.md             # How to add or edit profiles
└── README.md
```

## About CCM

The Center for Cooperative Media is a grant-funded program based at Montclair State University's School of Communication and Media. It works to grow and strengthen local media through collaboration, training, shared services, and cooperative projects.

- **Director:** Stefanie Murray
- **Flagship program:** [NJ News Commons](https://centerforcooperativemedia.org/njnewscommons/) -- a network of 300+ news and information providers across New Jersey
- **Website:** [centerforcooperativemedia.org](https://centerforcooperativemedia.org/)

## Staff profiles

Each staff profile follows a standard format:

- Name, title, email, social links
- Background and education
- Areas of focus
- Role at CCM

Browse them in [`ccm-profiles/staff/`](ccm-profiles/staff/).

## Project profiles

Each project profile includes:

- Type, scope, website, membership info
- Overview and key features
- History, funders, and staff leads

Browse them in [`ccm-profiles/projects/`](ccm-profiles/projects/).

## Mamdani video analysis

A content analysis of ~76 videos from NYC Mayor Zohran Mamdani's social media accounts (Twitter/X, TikTok, YouTube, Instagram, Facebook), covering November 2025 through April 2026.

**Pipeline:** Download videos with yt-dlp, transcribe with Whisper (GPU-accelerated), extract frames at 3-second intervals, analyze on-screen text with AI vision, run keyword-based topic/sentiment analysis, and present results in an interactive dashboard.

**Key findings (from transcript analysis):**
- Top topics: governance (4,115 mentions), economy (1,925), housing (1,830)
- Dominant tone: celebratory (30/76 videos), followed by persuasive (22/76)
- 307 minutes of video content, 47,448 words transcribed
- Facebook videos are longest (avg 12 min, mostly press conferences), while TikTok/Twitter/Instagram are short-form (avg 1-2 min)

**Dashboard:** Run `cd mamdani-video-analysis && python -m http.server 8888` and open `http://localhost:8888/web/index.html`.

See [`CLAUDE.md`](CLAUDE.md) for pipeline details and known issues.

## Annual reports

PDF annual reports from 2020--2024 are available at [centerforcooperativemedia.org/annual-reports/](https://centerforcooperativemedia.org/annual-reports/). They are not tracked in this repo due to file size. See [`reports/README.md`](reports/README.md) for details.

## Web archives

The `.firecrawl/` directory contains point-in-time snapshots of CCM website pages, scraped as markdown. These serve as reference material and are not automatically updated.

## License

This repository is licensed under [CC BY 4.0](LICENSE). You are free to share and adapt the contents with attribution.
