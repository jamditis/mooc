"""Re-analyze all transcripts via the Anthropic Batch API (Opus).

Usage:
    # Step 1: Create the batch
    python scripts/05-batch-analysis.py create

    # Step 2: Check status / retrieve results (run after batch completes)
    python scripts/05-batch-analysis.py results <batch_id>

    # Or do both in one shot (creates, polls, writes results):
    python scripts/05-batch-analysis.py run

Requires ANTHROPIC_API_KEY env var.
"""

import json
import re
import sys
import time
from pathlib import Path

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

BASE_DIR = Path(__file__).resolve().parent.parent
METADATA_FILE = BASE_DIR / "metadata.json"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
ANALYSIS_DIR = BASE_DIR / "analysis"
BATCH_DIR = BASE_DIR / "batch-results"

MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = """You are a political communications analyst. You will receive the transcript of a social media video posted by New York City Mayor Zohran Mamdani.

Analyze the transcript and return a JSON object with exactly this structure:

{
  "summary": "2-3 sentence summary of the video content",
  "topics": ["topic1", "topic2"],
  "topic_scores": {"topic1": 0.9, "topic2": 0.6},
  "sentiment": {
    "positive": 0.0,
    "negative": 0.0,
    "urgent": 0.0
  },
  "dominant_tone": "one of: positive, negative, urgent, informative, celebratory, persuasive, neutral",
  "key_messages": ["main point 1", "main point 2"],
  "audience": "who this video seems aimed at",
  "rhetorical_strategies": ["strategy1", "strategy2"]
}

Rules:
- topics: Use these canonical topic names when applicable: housing, transit, public_safety, education, economy, health, immigration, environment, budget, governance. You may also add other specific topics not in this list if they are prominent.
- topic_scores: A relevance score from 0.0 to 1.0 for each topic listed.
- sentiment: Normalized scores that sum to 1.0 across positive/negative/urgent. If the tone doesn't fit these three categories well, distribute as best you can.
- dominant_tone: Your overall assessment of the video's tone.
- key_messages: The 1-3 most important points or policy positions.
- audience: Brief description (e.g., "general NYC public", "progressive activists", "media/press corps").
- rhetorical_strategies: e.g., "direct address to camera", "personal anecdote", "call to action", "policy explanation", "humor", "emotional appeal".

Return ONLY valid JSON, no markdown fences, no commentary."""


def load_metadata():
    with open(METADATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_transcript(platform, video_id):
    txt_file = TRANSCRIPTS_DIR / platform / f"{video_id}.txt"
    if txt_file.exists():
        return txt_file.read_text(encoding="utf-8").strip()
    return None


def build_requests(metadata):
    """Build batch request list from metadata + transcripts."""
    requests = []
    skipped = 0

    for video in metadata["videos"]:
        vid_id = video["id"]
        platform = video["platform"]
        transcript = load_transcript(platform, vid_id)

        if not transcript or len(transcript.split()) < 3:
            skipped += 1
            continue

        title = video.get("title", "Untitled")
        duration = video.get("duration", 0)
        user_msg = (
            f"Platform: {platform}\n"
            f"Title: {title}\n"
            f"Duration: {duration:.0f} seconds\n\n"
            f"Transcript:\n{transcript}"
        )

        requests.append(
            Request(
                custom_id=f"{platform}__{vid_id}",
                params=MessageCreateParamsNonStreaming(
                    model=MODEL,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_msg}],
                ),
            )
        )

    print(f"Built {len(requests)} requests ({skipped} skipped)")
    return requests


def create_batch(client, requests):
    """Submit the batch and return the batch object."""
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch created: {batch.id}")
    print(f"Status: {batch.processing_status}")
    return batch


def poll_batch(client, batch_id):
    """Poll until batch completes. Returns the final batch object."""
    print(f"Polling batch {batch_id}...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        total = counts.succeeded + counts.errored + counts.canceled + counts.expired
        print(
            f"  {batch.processing_status} | "
            f"done: {total}/{total + counts.processing} | "
            f"ok: {counts.succeeded} err: {counts.errored}"
        )
        if batch.processing_status == "ended":
            return batch
        time.sleep(30)


def collect_results(client, batch_id):
    """Download batch results and return parsed per-video analyses."""
    results = {}
    errors = []

    for result in client.messages.batches.results(batch_id):
        custom_id = result.custom_id
        parts = custom_id.split("__", 1)
        if len(parts) != 2:
            errors.append(f"Bad custom_id: {custom_id}")
            continue
        platform, vid_id = parts

        if result.result.type == "succeeded":
            msg = result.result.message
            text = ""
            for block in msg.content:
                if block.type == "text":
                    text += block.text
            # Strip markdown fences if Claude wrapped the JSON
            cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
            cleaned = re.sub(r"\s*```\s*$", "", cleaned).strip()
            try:
                analysis = json.loads(cleaned)
                analysis["_platform"] = platform
                analysis["_video_id"] = vid_id
                results[vid_id] = analysis
            except json.JSONDecodeError as e:
                errors.append(f"{custom_id}: JSON parse error: {e}\nRaw: {text[:200]}")
        elif result.result.type == "errored":
            errors.append(f"{custom_id}: {result.result.error.type}")
        elif result.result.type == "expired":
            errors.append(f"{custom_id}: expired")
        elif result.result.type == "canceled":
            errors.append(f"{custom_id}: canceled")

    if errors:
        print(f"\n{len(errors)} errors:")
        for e in errors:
            print(f"  {e}")

    print(f"\nSuccessfully parsed {len(results)} video analyses")
    return results


def build_analysis_files(results, metadata):
    """Convert per-video Claude analyses into the dashboard JSON files."""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # --- topics.json ---
    overall_topics = {}
    per_platform_topics = {}
    per_video_topics = {}

    for video in metadata["videos"]:
        vid_id = video["id"]
        platform = video["platform"]
        if vid_id not in results:
            continue

        r = results[vid_id]
        scores = r.get("topic_scores", {})

        # Convert float scores to integer counts (multiply by 100 for granularity)
        int_scores = {}
        for topic, score in scores.items():
            int_score = max(1, round(float(score) * 100))
            int_scores[topic] = int_score
            overall_topics[topic] = overall_topics.get(topic, 0) + int_score
            if platform not in per_platform_topics:
                per_platform_topics[platform] = {}
            per_platform_topics[platform][topic] = (
                per_platform_topics[platform].get(topic, 0) + int_score
            )

        per_video_topics[vid_id] = {
            "title": video.get("title", ""),
            "platform": platform,
            "topics": int_scores,
        }

    # Sort overall by count descending
    overall_sorted = dict(sorted(overall_topics.items(), key=lambda x: -x[1]))
    per_platform_sorted = {
        p: dict(sorted(t.items(), key=lambda x: -x[1]))
        for p, t in per_platform_topics.items()
    }

    topics_json = {
        "overall": overall_sorted,
        "per_platform": per_platform_sorted,
        "per_video": per_video_topics,
    }

    # --- sentiment.json ---
    per_video_sentiment = {}
    per_platform_sentiment = {}

    for video in metadata["videos"]:
        vid_id = video["id"]
        platform = video["platform"]
        if vid_id not in results:
            continue

        r = results[vid_id]
        sent = r.get("sentiment", {"positive": 0.33, "negative": 0.33, "urgent": 0.34})

        # Convert normalized floats to raw counts (scale by word count for compatibility)
        transcript_file = TRANSCRIPTS_DIR / platform / f"{vid_id}.txt"
        word_count = 0
        if transcript_file.exists():
            word_count = len(transcript_file.read_text(encoding="utf-8").split())

        # Scale sentiment proportions into pseudo-counts
        scale = max(word_count // 50, 1)
        raw = {
            "positive": round(float(sent.get("positive", 0)) * scale),
            "negative": round(float(sent.get("negative", 0)) * scale),
            "urgent": round(float(sent.get("urgent", 0)) * scale),
        }

        total = sum(raw.values()) or 1
        normalized = {k: round(v / total, 3) for k, v in raw.items()}

        per_video_sentiment[vid_id] = {
            "title": video.get("title", ""),
            "platform": platform,
            "raw_counts": raw,
            "normalized": normalized,
            "dominant_tone": r.get("dominant_tone", "neutral"),
            "word_count": word_count,
            "summary": r.get("summary", ""),
            "key_messages": r.get("key_messages", []),
            "audience": r.get("audience", ""),
            "rhetorical_strategies": r.get("rhetorical_strategies", []),
        }

        if platform not in per_platform_sentiment:
            per_platform_sentiment[platform] = {
                "positive": 0, "negative": 0, "urgent": 0, "count": 0,
            }
        for tone in ["positive", "negative", "urgent"]:
            per_platform_sentiment[platform][tone] += raw[tone]
        per_platform_sentiment[platform]["count"] += 1

    sentiment_json = {
        "per_video": per_video_sentiment,
        "per_platform": per_platform_sentiment,
    }

    # --- cross-platform.json (keep existing, this script doesn't change it) ---
    # The cross-platform file uses word frequencies and frame analysis data
    # that don't change with Claude analysis. Leave it as-is.

    # --- summary.json ---
    total_videos = len(metadata["videos"])
    total_duration = sum(v.get("duration", 0) for v in metadata["videos"])
    platforms = list(set(v["platform"] for v in metadata["videos"]))

    # Get top topics from Claude analysis
    top_topics = list(overall_sorted.keys())[:5]

    tone_counts = {}
    for vid_data in per_video_sentiment.values():
        tone = vid_data["dominant_tone"]
        tone_counts[tone] = tone_counts.get(tone, 0) + 1

    total_words = sum(
        v.get("word_count", 0) for v in per_video_sentiment.values()
    )

    summary_json = {
        "total_videos": total_videos,
        "total_duration_seconds": total_duration,
        "total_duration_minutes": round(total_duration / 60, 1),
        "platforms": platforms,
        "platform_count": len(platforms),
        "top_topics": top_topics,
        "dominant_tone_distribution": tone_counts,
        "videos_per_platform": {},
        "total_words": total_words,
    }
    for v in metadata["videos"]:
        p = v["platform"]
        summary_json["videos_per_platform"][p] = (
            summary_json["videos_per_platform"].get(p, 0) + 1
        )

    # Write files
    with open(ANALYSIS_DIR / "topics.json", "w", encoding="utf-8") as f:
        json.dump(topics_json, f, indent=2)
    with open(ANALYSIS_DIR / "sentiment.json", "w", encoding="utf-8") as f:
        json.dump(sentiment_json, f, indent=2)
    with open(ANALYSIS_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)

    print(f"Wrote topics.json, sentiment.json, summary.json to {ANALYSIS_DIR}/")
    print(f"  cross-platform.json left unchanged (uses word freq + frame data)")

    # Also save raw Claude results for reference
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    with open(BATCH_DIR / "claude-analysis-raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"  Raw Claude results saved to {BATCH_DIR}/claude-analysis-raw.json")


def cmd_create(client):
    metadata = load_metadata()
    requests = build_requests(metadata)
    batch = create_batch(client, requests)
    print(f"\nBatch ID: {batch.id}")
    print("Run this to get results when done:")
    print(f"  python scripts/05-batch-analysis.py results {batch.id}")
    return batch.id


def cmd_results(client, batch_id):
    batch = client.messages.batches.retrieve(batch_id)
    if batch.processing_status != "ended":
        print(f"Batch not done yet: {batch.processing_status}")
        print(f"  processing: {batch.request_counts.processing}")
        return

    results = collect_results(client, batch_id)
    metadata = load_metadata()
    build_analysis_files(results, metadata)


def cmd_run(client):
    metadata = load_metadata()
    requests = build_requests(metadata)
    batch = create_batch(client, requests)
    batch = poll_batch(client, batch.id)

    results = collect_results(client, batch.id)
    build_analysis_files(results, metadata)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/05-batch-analysis.py create")
        print("  python scripts/05-batch-analysis.py results <batch_id>")
        print("  python scripts/05-batch-analysis.py run")
        sys.exit(1)

    client = anthropic.Anthropic()
    command = sys.argv[1]

    if command == "create":
        cmd_create(client)
    elif command == "results":
        if len(sys.argv) < 3:
            print("Error: batch_id required")
            sys.exit(1)
        cmd_results(client, sys.argv[2])
    elif command == "run":
        cmd_run(client)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
