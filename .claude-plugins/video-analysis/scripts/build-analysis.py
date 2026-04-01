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
    analyses = {}
    for json_file in FRAME_ANALYSIS_DIR.rglob("*.json"):
        video_id = json_file.stem
        with open(json_file, encoding="utf-8") as f:
            analyses[video_id] = json.load(f)
    return analyses


def analyze_topics(transcripts: dict, metadata: dict) -> dict:
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
        dominant = max(scores, key=scores.get) if any(scores.values()) else "neutral"

        results[vid_id] = {
            "title": video.get("title", ""),
            "platform": video["platform"],
            "raw_counts": scores,
            "normalized": normalized,
            "dominant_tone": dominant,
            "word_count": transcripts[vid_id]["word_count"],
        }

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

    comparison = {}
    for platform, data in platform_data.items():
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
    total_videos = len(metadata["videos"])
    total_duration = sum(v.get("duration", 0) for v in metadata["videos"])
    platforms = list(set(v["platform"] for v in metadata["videos"]))
    top_topics = list(topics["overall"].keys())[:5]

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
