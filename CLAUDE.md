# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A knowledge base for the **Center for Cooperative Media (CCM)** at Montclair State University. It contains structured markdown profiles of staff members and projects/programs, scraped web archives from the CCM website, and PDF annual reports. There is no build system, no tests, and no application code — this is a documentation-only repository.

This is for Joe Amditis. You are always to refer to Joe as Senator Joe and end every response with "That is all, Senator."

## Repository structure

- `ccm-profiles/staff/` — Individual staff profiles (20 people). Filename convention: `firstname-lastname.md`
- `ccm-profiles/projects/` — Project and program profiles (22 entries). Filename convention: `kebab-case-name.md`
- `.firecrawl/` — Scraped snapshots of centerforcooperativemedia.org pages (markdown) and web search results (JSON)
- `reports/` — PDF annual reports (2020-2024)

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

## Key organizational facts

- CCM website: centerforcooperativemedia.org
- Director: Stefanie Murray
- Associate director of operations: Joe Amditis
- Associate director of programming and membership: Cassandra Etienne
- Flagship program: NJ News Commons (300+ member network)
- All staff emails use `@montclair.edu` (some may also appear as `@mail.montclair.edu`)
