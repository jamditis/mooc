# mooc

Knowledge base for the [Center for Cooperative Media](https://centerforcooperativemedia.org/) (CCM) at Montclair State University.

Structured markdown profiles of CCM staff and programs, scraped web archives, and references to annual reports. This is a documentation-only repository -- no application code.

## What's in here

```
mooc/
├── ccm-profiles/
│   ├── staff/          # 20 staff profiles
│   └── projects/       # 22 project/program profiles
├── .firecrawl/         # 13 scraped web snapshots (markdown + JSON)
├── reports/            # Annual reports (PDFs not tracked -- see reports/README.md)
├── CLAUDE.md           # Claude Code project instructions
├── CONTRIBUTING.md     # How to add or edit profiles
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

## Annual reports

PDF annual reports from 2020--2024 are available at [centerforcooperativemedia.org/annual-reports/](https://centerforcooperativemedia.org/annual-reports/). They are not tracked in this repo due to file size. See [`reports/README.md`](reports/README.md) for details.

## Web archives

The `.firecrawl/` directory contains point-in-time snapshots of CCM website pages, scraped as markdown. These serve as reference material and are not automatically updated.

## License

This repository is licensed under [CC BY 4.0](LICENSE). You are free to share and adapt the contents with attribution.
