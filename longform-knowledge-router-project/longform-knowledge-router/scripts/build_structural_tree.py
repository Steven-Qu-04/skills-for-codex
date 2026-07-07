#!/usr/bin/env python3
import argparse, json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--source-spans", required=True)
p.add_argument("--output-dir", required=True)
args = p.parse_args()
spans = [json.loads(line) for line in Path(args.source_spans).read_text(encoding="utf-8").splitlines() if line.strip()]
tree = {"artifact_status": "complete", "nodes": []}
for span in spans:
    tree["nodes"].append({
        "source_span_id": span["source_span_id"],
        "structural_path": span.get("structural_path", []),
        "markdown_anchor": span.get("markdown_anchor"),
    })
out = Path(args.output_dir)
out.mkdir(parents=True, exist_ok=True)
(out / "structural_tree.json").write_text(json.dumps(tree, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
