#!/usr/bin/env python3
import argparse, json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--output-dir", required=True)
p.add_argument("--reason", default="manual repair requested")
args = p.parse_args()
out = Path(args.output_dir)
out.mkdir(parents=True, exist_ok=True)
row = {"repair_suggestion_id": "repair_manual", "type": "manual_repair", "reason": args.reason}
with (out / "repair_suggestions.jsonl").open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
