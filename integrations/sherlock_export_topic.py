#!/usr/bin/env python3
"""
Export a compact JSONL "topic packet" from Sherlock datasets
for downstream cross-reference by ChatGPT or Claude.
"""
import argparse, json, pathlib, re

def scrape_texts(root, topic):
    records = []
    for p in pathlib.Path(root).rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".json", ".csv"}:
            try:
                txt = p.read_text(errors="ignore")
            except Exception:
                continue
            if re.search(topic, txt, re.IGNORECASE):
                records.append({"path": str(p), "excerpt": txt[:4000]})
    return records

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # Sherlock dataset roots
    roots = [
        "evidence",
        "research_outputs",
        "uap_science_checkpoints",
        "jfk_checkpoints",
        "italy_ufo_checkpoints"
    ]
    recs = []
    for r in roots:
        if pathlib.Path(r).exists():
            recs += scrape_texts(r, args.topic)

    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps({"topic": args.topic, **r}) + "\n")

    print(f"Exported {len(recs)} records to {args.out}")

if __name__ == "__main__":
    main()
