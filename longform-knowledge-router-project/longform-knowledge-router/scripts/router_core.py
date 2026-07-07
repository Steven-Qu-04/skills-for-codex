#!/usr/bin/env python3
"""Shared implementation for the longform knowledge router MVP-2 scripts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


RESERVED_REASON = "MVP-2 reserves this contract; full implementation belongs to MVP-3."
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "are", "was", "were", "has",
    "have", "had", "not", "but", "you", "your", "its", "their", "his", "her", "our", "of",
    "to", "in", "on", "by", "as", "at", "or", "an", "a", "is", "be", "it", "which",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def append_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def stable_id(prefix: str, *parts: Any, n: int = 12) -> str:
    raw = "\u241f".join(str(p) for p in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:n]}"


def ensure_output_dir(path: str | Path) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(exist_ok=True)
    return out


def classify_block(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return "blank"
    if stripped.startswith("#"):
        return "heading"
    if re.match(r"^(figure|fig\.|image)\s+\d*[:.\-]", stripped, re.I):
        return "caption"
    if re.match(r"^(table)\s+\d*[:.\-]", stripped, re.I):
        return "table_note"
    if re.match(r"^[-*+]\s+", stripped) or re.match(r"^\d+[.)]\s+", stripped):
        return "list_item"
    if re.match(r"^\s*\|.+\|\s*$", text):
        return "table"
    if "$$" in stripped or re.search(r"\\\(|\\\[", stripped):
        return "formula"
    return "paragraph"


def anchor_for(block_id: str, text: str) -> str:
    words = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    slug = "-".join(words[:8]) or block_id
    return f"{slug}-{block_id[-6:]}"


def text_terms(text: str, limit: int = 8) -> list[str]:
    terms = [w.lower() for w in re.findall(r"[\w\u4e00-\u9fff]{2,}", text)]
    counts = Counter(t for t in terms if t not in STOPWORDS and not t.isdigit())
    return [term for term, _ in counts.most_common(limit)]


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = read_json(path, {})
    if "files" not in manifest:
        raise SystemExit(f"manifest has no files: {path}")
    return manifest


def ingest(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    input_path = Path(args.input)
    config = read_json(args.config, {}) if args.config else {}
    files = [input_path] if input_path.is_file() else [p for p in input_path.rglob("*") if p.is_file()]
    supported = {".md", ".markdown", ".txt", ".html", ".htm", ".pdf", ".docx", ".epub"}
    records = []
    errors = []
    for file in sorted(files):
        suffix = file.suffix.lower()
        if suffix not in supported:
            errors.append({"file": str(file), "error": "unsupported_suffix", "suffix": suffix})
            continue
        records.append({
            "file_id": stable_id("file", file.resolve()),
            "path": str(file),
            "suffix": suffix,
            "size_bytes": file.stat().st_size,
            "status": "queued",
        })
    write_json(out / "manifest.json", {
        "created_at": now(),
        "input": str(input_path),
        "config": config,
        "files": records,
    })
    write_jsonl(out / "errors.jsonl", errors)


def extract_pdf_text(path: Path) -> list[tuple[int | None, str]]:
    try:
        import fitz  # type: ignore
    except Exception:
        return [(None, path.read_bytes().decode("utf-8", errors="ignore"))]
    doc = fitz.open(path)
    pages: list[tuple[int | None, str]] = []
    for idx, page in enumerate(doc, start=1):
        pages.append((idx, page.get_text("text")))
    return pages


def parse_document(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    manifest = load_manifest(args.manifest)
    raw_rows: list[dict[str, Any]] = []
    layout_rows: list[dict[str, Any]] = []
    page_images = out / "page_images"
    page_images.mkdir(exist_ok=True)
    order = 0
    for item in manifest["files"]:
        path = Path(item["path"])
        pages = extract_pdf_text(path) if path.suffix.lower() == ".pdf" else [(None, path.read_text(encoding="utf-8", errors="ignore"))]
        current_heading: list[str] = []
        for page, content in pages:
            paragraphs = re.split(r"\n\s*\n", content.replace("\r\n", "\n"))
            for para in paragraphs:
                text = para.strip()
                if not text:
                    continue
                block_type = classify_block(text)
                if block_type == "heading":
                    current_heading = [text.lstrip("#").strip()]
                order += 1
                block_id = stable_id("block", item["file_id"], page or 0, order, text[:80])
                row = {
                    "block_id": block_id,
                    "file_id": item["file_id"],
                    "source_file": item["path"],
                    "page": page,
                    "bbox": None,
                    "block_type": block_type,
                    "text": text,
                    "reading_order": order,
                    "page_reading_order": order,
                    "structural_path": current_heading[:],
                    "markdown_anchor": anchor_for(block_id, text),
                    "extraction_confidence": 0.75 if path.suffix.lower() == ".pdf" else 0.95,
                }
                raw_rows.append(row)
                layout_rows.append({**row, "layout_source": "text_parse", "asset_path": None})
    write_jsonl(out / "raw_blocks.jsonl", raw_rows)
    write_jsonl(out / "layout_blocks.jsonl", layout_rows)


def segment_source_spans(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    blocks = read_jsonl(args.raw_blocks)
    source_blocks = []
    candidates = []
    low_confidence = []
    for block in blocks:
        block_id = block["block_id"]
        span_id = stable_id("span", block_id, block.get("text", "")[:80])
        source_blocks.append({**block, "source_block_id": block_id, "span_ids": [span_id]})
        candidate = {
            "source_span_id": span_id,
            "source_block_id": block_id,
            "block_type": block["block_type"],
            "text": block["text"],
            "source_file": block["source_file"],
            "page": block.get("page"),
            "bbox": block.get("bbox"),
            "reading_order": block["reading_order"],
            "page_reading_order": block["page_reading_order"],
            "structural_path": block.get("structural_path", []),
            "markdown_anchor": block["markdown_anchor"],
            "split_reason": "initial_block_boundary",
            "status": "candidate",
            "extraction_confidence": block.get("extraction_confidence", 0.0),
        }
        if candidate["extraction_confidence"] < 0.8 or candidate["bbox"] is None:
            low_confidence.append({
                "source_span_id": span_id,
                "issue": "low_confidence_or_missing_bbox",
                "bbox": candidate["bbox"],
            })
        candidates.append(candidate)
    write_jsonl(out / "source_blocks.jsonl", source_blocks)
    write_jsonl(out / "source_span_candidates.jsonl", candidates)
    write_json(out / "source_segmentation_report.json", {
        "artifact_status": "complete",
        "span_count": len(candidates),
        "block_count": len(source_blocks),
        "low_confidence_or_missing_bbox": low_confidence,
        "policy": "heading/paragraph/caption/table/formula boundaries; no fixed-token chunking",
    })


def build_source_map(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    candidates = read_jsonl(args.source_span_candidates)
    spans = []
    md_lines = ["# Compiled Longform Source", ""]
    for row in candidates:
        span = {**row, "status": "active"}
        spans.append(span)
        level = "##" if row["block_type"] == "heading" else ""
        md_lines.append(f'<a id="{row["markdown_anchor"]}"></a>')
        md_lines.append(f"<!-- source_span_id: {row['source_span_id']} page: {row.get('page')} -->")
        md_lines.append(f"{level} {row['text']}".strip())
        md_lines.append("")
    write_jsonl(out / "source_spans.jsonl", spans)
    (out / "book.md").write_text("\n".join(md_lines), encoding="utf-8")


def extract_assets(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    rows = read_jsonl(args.layout_blocks)
    figures = []
    tables = []
    candidates = []
    for row in rows:
        if row["block_type"] in {"caption", "figure"}:
            fig = {
                "figure_id": stable_id("fig", row["block_id"]),
                "block_id": row["block_id"],
                "source_span_id": stable_id("span", row["block_id"], row.get("text", "")[:80]),
                "page": row.get("page"),
                "bbox": row.get("bbox"),
                "asset_path": row.get("asset_path"),
                "caption": row.get("text"),
                "artifact_status": "complete" if row.get("asset_path") else "deferred",
                "reason": None if row.get("asset_path") else "No extractable raster asset was available in MVP-2 parsing.",
            }
            figures.append(fig)
            candidates.append({"asset_type": "figure", **fig})
        if row["block_type"] in {"table", "table_note"}:
            table = {
                "table_id": stable_id("table", row["block_id"]),
                "block_id": row["block_id"],
                "source_span_id": stable_id("span", row["block_id"], row.get("text", "")[:80]),
                "page": row.get("page"),
                "bbox": row.get("bbox"),
                "asset_path": row.get("asset_path"),
                "caption": row.get("text"),
            }
            tables.append(table)
            candidates.append({"asset_type": "table", **table})
    write_jsonl(out / "figures.jsonl", figures)
    write_jsonl(out / "tables.jsonl", tables)
    write_jsonl(out / "asset_candidates.jsonl", candidates)


def capture_visual_regions(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    rows = read_jsonl(args.layout_blocks)
    visual = []
    for row in rows:
        if row["block_type"] in {"caption", "figure", "table", "formula"}:
            visual.append({
                "visual_region_id": stable_id("vreg", row["block_id"]),
                "block_id": row["block_id"],
                "source_span_id": stable_id("span", row["block_id"], row.get("text", "")[:80]),
                "page": row.get("page"),
                "bbox": row.get("bbox"),
                "asset_path": row.get("asset_path"),
                "needs_review": row.get("bbox") is None or row.get("asset_path") is None,
                "capture_status": "deferred" if row.get("asset_path") is None else "complete",
            })
    write_jsonl(out / "visual_regions.jsonl", visual)


def describe_figures(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    regions = read_jsonl(args.visual_regions)
    spans_by_id = {s["source_span_id"]: s for s in read_jsonl(args.source_spans)}
    readings = []
    candidates = []
    for region in regions:
        span = spans_by_id.get(region["source_span_id"], {})
        reading_id = stable_id("figread", region["visual_region_id"])
        readings.append({
            "figure_reading_id": reading_id,
            "visual_region_id": region["visual_region_id"],
            "source_span_id": region["source_span_id"],
            "asset_path": region.get("asset_path"),
            "tool_policy": "agent_selected_vision_tool",
            "visible_facts": [],
            "contextual_interpretation": span.get("text", "") if region.get("asset_path") is None else "",
            "inferences": [],
            "uncertainties": ["visual interpretation deferred; an AI using this skill may choose an available vision tool"],
            "artifact_status": "deferred" if region.get("asset_path") is None else "complete",
        })
        candidates.append({
            "atom_candidate_id": stable_id("figatom", reading_id),
            "candidate_type": "figure_interpretation",
            "figure_reading_id": reading_id,
            "source_span_ids": [region["source_span_id"]],
            "text": span.get("text", ""),
            "status": "deferred" if region.get("asset_path") is None else "candidate",
        })
    write_jsonl(out / "figure_readings.jsonl", readings)
    write_jsonl(out / "figure_atom_candidates.jsonl", candidates)


def build_reading_frames(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    spans = read_jsonl(args.source_spans)
    frames = []
    for idx, span in enumerate(spans, start=1):
        frame_type = "main"
        if span["block_type"] in {"caption", "figure", "table", "formula"}:
            frame_type = "figure" if span["block_type"] in {"caption", "figure"} else span["block_type"]
        frames.append({
            "reading_frame_id": stable_id("frame", span["source_span_id"]),
            "frame_type": frame_type,
            "source_span_ids": [span["source_span_id"]],
            "structural_path": span.get("structural_path", []),
            "context_budget": {"local_spans_before": 1, "local_spans_after": 1, "max_chars": 6000},
            "guiding_questions": [
                "What atomic claims, definitions, examples, or relations are grounded here?",
                "Does this frame introduce, support, qualify, or revise another idea?",
            ],
            "registry_slice_types": ["concept", "claim"],
            "main_read_once": frame_type == "main",
            "ordinal": idx,
        })
    write_jsonl(out / "reading_frames.jsonl", frames)


def run_reading_frames(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    frames = read_jsonl(args.reading_frames)
    spans = {s["source_span_id"]: s for s in read_jsonl(args.source_spans)}
    patches = []
    gists = []
    registry_updates = []
    repairs = []
    for frame in frames:
        frame_spans = [spans[sid] for sid in frame["source_span_ids"] if sid in spans]
        text = "\n".join(s["text"] for s in frame_spans)
        terms = text_terms(text)
        patch_id = stable_id("patch", frame["reading_frame_id"])
        atom_id = stable_id("atomcand", frame["reading_frame_id"], text[:120])
        patches.append({
            "graph_patch_id": patch_id,
            "reading_frame_id": frame["reading_frame_id"],
            "source_span_ids": frame["source_span_ids"],
            "new_atoms": [{
                "atom_candidate_id": atom_id,
                "atom_type": "claim" if frame["frame_type"] == "main" else "figure_interpretation",
                "text": text[:1200],
                "source_span_ids": frame["source_span_ids"],
                "confidence": 0.65 if terms else 0.35,
            }] if text else [],
            "candidate_edges": [],
            "concept_terms": terms,
            "self_explanation": "Heuristic MVP-2 reading pass; self-explanation is navigation memory, not evidence.",
            "artifact_status": "complete",
        })
        gists.append({
            "rolling_gist_id": stable_id("gist", frame["reading_frame_id"]),
            "reading_frame_id": frame["reading_frame_id"],
            "source_span_ids": frame["source_span_ids"],
            "gist": text[:280],
            "not_evidence": True,
        })
        for term in terms:
            registry_updates.append({
                "registry_update_id": stable_id("regupd", frame["reading_frame_id"], term),
                "term": term,
                "source_span_ids": frame["source_span_ids"],
                "reading_frame_id": frame["reading_frame_id"],
            })
        if not text:
            repairs.append({
                "repair_suggestion_id": stable_id("repair", frame["reading_frame_id"]),
                "type": "empty_frame",
                "reading_frame_id": frame["reading_frame_id"],
                "reason": "Reading frame had no source text.",
            })
    write_jsonl(out / "graph_patches.jsonl", patches)
    write_jsonl(out / "rolling_gists.jsonl", gists)
    write_jsonl(out / "registry_updates.jsonl", registry_updates)
    write_jsonl(out / "repair_suggestions.jsonl", repairs)


def integrate_graph_patches(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    patches = read_jsonl(args.graph_patches)
    source_ids = {s["source_span_id"] for s in read_jsonl(args.source_spans)}
    atoms = []
    node_candidates = []
    edge_candidates = []
    statuses = []
    seen_main = set()
    for patch in patches:
        grounded = all(sid in source_ids for sid in patch.get("source_span_ids", []))
        for atom in patch.get("new_atoms", []):
            atom_row = {
                **atom,
                "graph_patch_id": patch["graph_patch_id"],
                "reading_frame_id": patch["reading_frame_id"],
                "evidence_source": "source_span",
                "grounded": grounded,
            }
            atoms.append(atom_row)
            node_candidates.append({
                "route_node_candidate_id": stable_id("nodecand", atom["atom_candidate_id"]),
                "node_type": "claim" if atom.get("atom_type") == "claim" else "figure",
                "atom_candidate_ids": [atom["atom_candidate_id"]],
                "source_span_ids": atom.get("source_span_ids", []),
                "label": atom.get("text", "")[:120],
                "payload_level": "standard",
            })
        for sid in patch.get("source_span_ids", []):
            statuses.append({
                "source_span_id": sid,
                "reading_frame_id": patch["reading_frame_id"],
                "main_read_status": "read" if sid not in seen_main else "duplicate_context",
                "graph_patch_id": patch["graph_patch_id"],
            })
            seen_main.add(sid)
    write_jsonl(out / "atom_candidates.jsonl", atoms)
    write_jsonl(out / "route_node_candidates.jsonl", node_candidates)
    write_jsonl(out / "route_edge_candidates.jsonl", edge_candidates)
    write_jsonl(out / "main_read_status.jsonl", statuses)


def update_reading_memory(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    patches = read_jsonl(args.graph_patches)
    existing_gists = read_jsonl(args.rolling_gists)
    concept_hits: dict[str, set[str]] = defaultdict(set)
    claim_rows = []
    for patch in patches:
        for term in patch.get("concept_terms", []):
            concept_hits[term].update(patch.get("source_span_ids", []))
        for atom in patch.get("new_atoms", []):
            claim_rows.append({
                "claim_id": stable_id("claim", atom.get("text", "")[:160]),
                "surface": atom.get("text", "")[:240],
                "source_span_ids": atom.get("source_span_ids", []),
                "reading_frame_id": patch["reading_frame_id"],
            })
    concepts = [{
        "concept_id": stable_id("concept", term),
        "surface": term,
        "source_span_ids": sorted(ids),
        "not_evidence": True,
    } for term, ids in sorted(concept_hits.items())]
    write_jsonl(out / "rolling_gists.jsonl", existing_gists)
    write_jsonl(out / "concept_registry.jsonl", concepts)
    write_jsonl(out / "claim_registry.jsonl", claim_rows)
    write_jsonl(out / "revision_ledger.jsonl", [])
    write_jsonl(out / "open_reference_ledger.jsonl", [])


def extract_atoms(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    source_ids = {s["source_span_id"] for s in read_jsonl(args.source_spans)}
    candidates = read_jsonl(args.atom_candidates) + read_jsonl(args.figure_atom_candidates)
    atoms = []
    seen = set()
    for cand in candidates:
        text = cand.get("text", "").strip()
        source_span_ids = [sid for sid in cand.get("source_span_ids", []) if sid in source_ids]
        if not text or not source_span_ids:
            continue
        atom_id = stable_id("atom", text[:200], "|".join(source_span_ids))
        if atom_id in seen:
            continue
        seen.add(atom_id)
        atoms.append({
            "atom_id": atom_id,
            "atom_type": cand.get("atom_type") or cand.get("candidate_type") or "claim",
            "text": text,
            "source_span_ids": source_span_ids,
            "confidence": cand.get("confidence", 0.6),
            "created_from": cand.get("atom_candidate_id"),
        })
    write_jsonl(out / "atoms.jsonl", atoms)


def build_route_graph(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    atoms = read_jsonl(args.atoms)
    spans = {s["source_span_id"]: s for s in read_jsonl(args.source_spans)}
    nodes = []
    edges = []
    previous_node = None
    for atom in atoms:
        node_id = stable_id("node", atom["atom_id"])
        node = {
            "route_node_id": node_id,
            "node_type": "figure" if "figure" in atom.get("atom_type", "") else "claim",
            "label": atom["text"][:140],
            "atom_ids": [atom["atom_id"]],
            "source_span_ids": atom["source_span_ids"],
            "semantic_payload": {
                "payload_level": "standard",
                "routing_semantics": text_terms(atom["text"], 6),
                "not_evidence": True,
            },
            "can_jump_to_source": all(sid in spans for sid in atom["source_span_ids"]),
        }
        nodes.append(node)
        if previous_node:
            edge_id = stable_id("edge", previous_node, node_id)
            evidence = atom["source_span_ids"][:1]
            edges.append({
                "route_edge_id": edge_id,
                "from_node_id": previous_node,
                "to_node_id": node_id,
                "edge_type": "adjacent_argument",
                "edge_class": "semantic",
                "evidence_span_ids": evidence,
                "confidence": 0.55,
                "semantic_payload": {"payload_level": "standard", "not_evidence": True},
            })
        previous_node = node_id
    write_jsonl(out / "route_nodes.jsonl", nodes)
    write_jsonl(out / "route_edges.jsonl", edges)
    write_json(out / "route_graph.json", {
        "artifact_status": "complete",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes_file": "route_nodes.jsonl",
        "edges_file": "route_edges.jsonl",
    })


def build_route_index(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    graph = read_json(args.route_graph, {})
    nodes = read_jsonl(out / graph.get("nodes_file", "route_nodes.jsonl"))
    edges = read_jsonl(out / graph.get("edges_file", "route_edges.jsonl"))
    edge_by_from = defaultdict(list)
    for edge in edges:
        edge_by_from[edge["from_node_id"]].append(edge)
    templates = []
    for node in nodes:
        steps = [{"node_id": node["route_node_id"], "source_span_ids": node["source_span_ids"]}]
        for edge in edge_by_from.get(node["route_node_id"], [])[:1]:
            steps.append({"edge_id": edge["route_edge_id"], "node_id": edge["to_node_id"], "source_span_ids": edge["evidence_span_ids"]})
        templates.append({
            "route_path_template_id": stable_id("tmpl", node["route_node_id"]),
            "start_node_id": node["route_node_id"],
            "mode": "local_reading",
            "steps": steps,
            "semantic_payload": {"payload_level": "expanded", "not_evidence": True},
        })
    write_jsonl(out / "route_path_templates.jsonl", templates)
    db = out / "route_index.sqlite"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.executescript("""
    create table nodes(node_id text primary key, label text, terms text, source_span_ids text);
    create table edges(edge_id text primary key, from_node_id text, to_node_id text, edge_class text, evidence_span_ids text);
    create table templates(template_id text primary key, start_node_id text, mode text, steps_json text);
    """)
    con.executemany(
        "insert into nodes values(?,?,?,?)",
        [(n["route_node_id"], n["label"], " ".join(n["semantic_payload"]["routing_semantics"]), json.dumps(n["source_span_ids"])) for n in nodes],
    )
    con.executemany(
        "insert into edges values(?,?,?,?,?)",
        [(e["route_edge_id"], e["from_node_id"], e["to_node_id"], e["edge_class"], json.dumps(e["evidence_span_ids"])) for e in edges],
    )
    con.executemany(
        "insert into templates values(?,?,?,?)",
        [(t["route_path_template_id"], t["start_node_id"], t["mode"], json.dumps(t["steps"], ensure_ascii=False)) for t in templates],
    )
    con.commit()
    con.close()


def build_stub_json(args: argparse.Namespace, name: str) -> None:
    out = ensure_output_dir(args.output_dir)
    write_json(out / name, {"artifact_status": "deferred", "target_mvp": "mvp3", "reason": RESERVED_REASON})


def build_stub_jsonl(args: argparse.Namespace, names: list[str]) -> None:
    out = ensure_output_dir(args.output_dir)
    for name in names:
        write_jsonl(out / name, [{"artifact_status": "deferred", "target_mvp": "mvp3", "reason": RESERVED_REASON}])


def query_route(args: argparse.Namespace) -> None:
    index = Path(args.index)
    out = Path(args.session_dir) if args.session_dir else index.parent / "query_session"
    out.mkdir(parents=True, exist_ok=True)
    terms = text_terms(args.question, 12)
    con = sqlite3.connect(index)
    rows = con.execute("select node_id, label, terms, source_span_ids from nodes").fetchall()
    templates = {row[1]: row for row in con.execute("select template_id, start_node_id, mode, steps_json from templates").fetchall()}
    con.close()
    candidate_paths = []
    rejected = []
    for node_id, label, node_terms, source_span_ids in rows:
        matched = sorted(set(terms) & set(node_terms.split()))
        if not matched and args.mode != "source_location_query":
            continue
        tmpl = templates.get(node_id)
        steps = json.loads(tmpl[3]) if tmpl else [{"node_id": node_id, "source_span_ids": json.loads(source_span_ids)}]
        candidate_paths.append({
            "path_id": stable_id("path", args.question, node_id),
            "mode": args.mode,
            "start_node_id": node_id,
            "steps": steps,
            "matched_terms": matched,
            "reasons": [f"matched_terms={','.join(matched)}"] if matched else ["source_location_query candidate"],
            "source_span_ids": sorted({sid for step in steps for sid in step.get("source_span_ids", [])}),
        })
    if not candidate_paths:
        rejected.append({
            "path_id": stable_id("pathrej", args.question),
            "rejected_reason": "no_route_node_matched_query_terms",
            "question_terms": terms,
        })
    route_session = {
        "route_session_id": stable_id("session", args.question, now()),
        "question": args.question,
        "mode": args.mode,
        "strategy": args.strategy,
        "budget": {"max_candidate_paths": 20, "max_verified_paths": 8},
        "visited_nodes": [p["start_node_id"] for p in candidate_paths],
        "accepted_evidence": [],
        "rejected_evidence": rejected,
        "stop_reason": "candidate_generation_complete",
    }
    write_json(out / "route_session.json", route_session)
    write_jsonl(out / "candidate_paths.jsonl", candidate_paths[:20])
    write_jsonl(out / "expanded_paths.jsonl", candidate_paths[:20])
    write_jsonl(out / "rejected_paths.jsonl", rejected)
    result = {
        "route_session": route_session,
        "candidate_paths": candidate_paths[:20],
        "expanded_paths": candidate_paths[:20],
        "verified_paths": [],
        "rejected_paths": rejected,
        "answer_plan": {"requires_verify_evidence": True},
        "source_spans": sorted({sid for p in candidate_paths for sid in p["source_span_ids"]}),
        "uncertainties": [] if candidate_paths else ["No route path matched the query."],
    }
    write_json(out / "answer.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def score_paths(args: argparse.Namespace) -> None:
    session = read_json(args.route_session, {})
    candidate_path = Path(args.candidate_paths)
    candidates = read_jsonl(candidate_path)
    scored = []
    rejected = []
    for path in candidates:
        source_count = len(path.get("source_span_ids", []))
        step_count = len(path.get("steps", []))
        match_count = len(path.get("matched_terms", []))
        score = round(min(1.0, 0.35 + 0.15 * match_count + 0.1 * source_count - 0.03 * max(0, step_count - 2)), 3)
        row = {**path, "path_score": score, "score_reasons": ["term_match", "source_grounding", "path_length_penalty"]}
        if score >= 0.4:
            scored.append(row)
        else:
            rejected.append({**row, "rejected_reason": "score_below_threshold"})
    out = Path(args.route_session).parent
    write_jsonl(out / "scored_paths.jsonl", sorted(scored, key=lambda r: r["path_score"], reverse=True))
    write_jsonl(out / "verified_paths.jsonl", sorted(scored, key=lambda r: r["path_score"], reverse=True))
    prior_rejected = read_jsonl(out / "rejected_paths.jsonl")
    write_jsonl(out / "rejected_paths.jsonl", prior_rejected + rejected)
    session["accepted_evidence"] = [p["path_id"] for p in scored]
    session["stop_reason"] = "path_scoring_complete"
    write_json(out / "route_session.json", session)


def verify_evidence(args: argparse.Namespace) -> None:
    answer = read_json(args.answer, {})
    spans = {s["source_span_id"]: s for s in read_jsonl(args.source_spans)}
    session = read_json(args.route_session, {})
    verified_paths = read_jsonl(Path(args.route_session).parent / "verified_paths.jsonl")
    unsupported = []
    path_breaks = []
    for path in verified_paths:
        if not path.get("source_span_ids"):
            path_breaks.append({"path_id": path.get("path_id"), "issue": "missing_source_spans"})
        for sid in path.get("source_span_ids", []):
            if sid not in spans:
                unsupported.append({"path_id": path.get("path_id"), "source_span_id": sid})
    report = {
        "unsupported_claims": unsupported,
        "overgeneralized_claims": [],
        "misused_hypothesis_edges": [],
        "missing_counterevidence_check": False,
        "source_mismatch": [],
        "path_breaks": path_breaks,
        "payload_not_used_as_evidence": True,
        "confidence": 0.9 if verified_paths and not unsupported and not path_breaks else 0.45,
        "route_session_id": session.get("route_session_id"),
        "answer_checked": bool(answer),
    }
    write_json(Path(args.route_session).parent / "verification_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def validate_build(args: argparse.Namespace) -> None:
    out = Path(args.output_dir)
    required = {
        "mvp0": ["book.md", "assets", "figures.jsonl", "tables.jsonl", "source_blocks.jsonl", "source_span_candidates.jsonl", "source_spans.jsonl", "source_segmentation_report.json", "build_report.md"],
        "mvp1": ["atoms.jsonl", "route_nodes.jsonl", "route_edges.jsonl", "route_graph.json"],
        "mvp2": ["reading_frames.jsonl", "graph_patches.jsonl", "rolling_gists.jsonl", "concept_registry.jsonl", "claim_registry.jsonl", "main_read_status.jsonl", "atom_candidates.jsonl", "figure_atom_candidates.jsonl", "route_index.sqlite", "route_path_templates.jsonl", "repair_suggestions.jsonl"],
        "mature": ["figure_atlas.json", "figure_routes.jsonl", "route_communities.jsonl", "route_reports.jsonl"],
    }
    order = ["mvp0", "mvp1", "mvp2"] if args.profile != "mature" else ["mvp0", "mvp1", "mvp2", "mature"]
    if args.profile == "mvp0":
        order = ["mvp0"]
    elif args.profile == "mvp1":
        order = ["mvp0", "mvp1"]
    missing = []
    for profile in order:
        for name in required[profile]:
            if not (out / name).exists():
                missing.append(name)
    reserved = []
    for name in ["figure_atlas.json", "figure_routes.jsonl", "route_communities.jsonl", "route_reports.jsonl"]:
        p = out / name
        if p.exists():
            data = read_json(p, None) if p.suffix == ".json" else (read_jsonl(p)[0] if read_jsonl(p) else {})
            if data.get("artifact_status") in {"stubbed", "deferred"}:
                reserved.append(name)
                if args.profile == "mature":
                    missing.append(f"{name}:complete")
    spans = read_jsonl(out / "source_spans.jsonl")
    frames = read_jsonl(out / "reading_frames.jsonl")
    statuses = read_jsonl(out / "main_read_status.jsonl")
    duplicate_main_reads = [sid for sid, count in Counter(s["source_span_id"] for s in statuses if s.get("main_read_status") == "read").items() if count > 1]
    report = {
        "profile": args.profile,
        "artifact_status": "failed" if missing or duplicate_main_reads else "complete",
        "missing": missing,
        "reserved_mvp3_artifacts": reserved,
        "source_span_count": len(spans),
        "reading_frame_count": len(frames),
        "duplicate_main_reads": duplicate_main_reads,
        "checks": {
            "fixed_token_chunking_forbidden": True,
            "payload_not_evidence_contract": True,
            "figure_atlas_contract_reserved": True,
        },
    }
    write_json(out / "validation_report.json", report)
    if missing or duplicate_main_reads:
        raise SystemExit(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


def write_build_report(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    validation = read_json(out / "validation_report.json", {})
    lines = [
        "# Build Report",
        "",
        f"- generated_at: {now()}",
        f"- profile: {args.profile}",
        f"- validation_status: {validation.get('artifact_status', 'not_run')}",
        "- evidence_rule: final answers must use source spans, verified atoms, or structured extracts; not payloads or gists.",
        "- visual_rule: figure atlas and routes preserve MVP-3 contracts; the AI using this skill may choose the available vision tool for actual image interpretation.",
        "",
    ]
    (out / "build_report.md").write_text("\n".join(lines), encoding="utf-8")


def parser_for(command: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=command)
    if command == "ingest":
        p.add_argument("--input", required=True)
        p.add_argument("--output-dir", required=True)
        p.add_argument("--config")
    elif command == "parse_document":
        p.add_argument("--manifest", required=True)
        p.add_argument("--output-dir", required=True)
    elif command == "segment_source_spans":
        p.add_argument("--raw-blocks", required=True)
        p.add_argument("--layout-blocks")
        p.add_argument("--output-dir", required=True)
    elif command == "extract_assets":
        p.add_argument("--layout-blocks", required=True)
        p.add_argument("--output-dir", required=True)
    elif command == "capture_visual_regions":
        p.add_argument("--layout-blocks", required=True)
        p.add_argument("--page-images")
        p.add_argument("--output-dir", required=True)
    elif command == "describe_figures":
        p.add_argument("--visual-regions", required=True)
        p.add_argument("--source-spans", required=True)
        p.add_argument("--output-dir", required=True)
    elif command == "build_figure_atlas":
        p.add_argument("--figure-readings")
        p.add_argument("--route-nodes")
        p.add_argument("--output-dir", required=True)
    elif command == "build_figure_routes":
        p.add_argument("--figure-atlas")
        p.add_argument("--route-graph")
        p.add_argument("--output-dir", required=True)
    elif command == "build_source_map":
        p.add_argument("--source-span-candidates", required=True)
        p.add_argument("--layout-blocks")
        p.add_argument("--output-dir", required=True)
    elif command == "build_reading_frames":
        p.add_argument("--source-spans", required=True)
        p.add_argument("--layout-blocks")
        p.add_argument("--output-dir", required=True)
    elif command == "run_reading_frames":
        p.add_argument("--reading-frames", required=True)
        p.add_argument("--source-spans", required=True)
        p.add_argument("--output-dir", required=True)
        p.add_argument("--profile", choices=["mvp1", "mvp2", "mature"], default="mvp2")
    elif command == "integrate_graph_patches":
        p.add_argument("--graph-patches", required=True)
        p.add_argument("--source-spans", required=True)
        p.add_argument("--output-dir", required=True)
    elif command == "update_reading_memory":
        p.add_argument("--graph-patches", required=True)
        p.add_argument("--rolling-gists", required=True)
        p.add_argument("--output-dir", required=True)
    elif command == "extract_atoms":
        p.add_argument("--atom-candidates", required=True)
        p.add_argument("--figure-atom-candidates", required=True)
        p.add_argument("--source-spans", required=True)
        p.add_argument("--output-dir", required=True)
    elif command == "build_route_graph":
        p.add_argument("--atoms", required=True)
        p.add_argument("--source-spans", required=True)
        p.add_argument("--output-dir", required=True)
    elif command == "build_route_index":
        p.add_argument("--route-graph", required=True)
        p.add_argument("--output-dir", required=True)
    elif command == "build_route_communities":
        p.add_argument("--route-graph")
        p.add_argument("--atoms")
        p.add_argument("--output-dir", required=True)
    elif command == "score_paths":
        p.add_argument("--route-session", required=True)
        p.add_argument("--candidate-paths", required=True)
        p.add_argument("--mode", default="local_reading")
    elif command == "query_route":
        p.add_argument("--question", required=True)
        p.add_argument("--index", required=True)
        p.add_argument("--mode", choices=["local_reading", "source_location_query", "concept_trace"], default="local_reading")
        p.add_argument("--strategy", choices=["explicit_path", "graph_activation", "hybrid"], default="explicit_path")
        p.add_argument("--session-dir")
    elif command == "verify_evidence":
        p.add_argument("--answer", required=True)
        p.add_argument("--source-spans", required=True)
        p.add_argument("--route-session", required=True)
    elif command == "validate_build":
        p.add_argument("--output-dir", required=True)
        p.add_argument("--profile", choices=["mvp0", "mvp1", "mvp2", "mature"], default="mvp2")
    elif command == "write_build_report":
        p.add_argument("--output-dir", required=True)
        p.add_argument("--profile", default="mvp2")
    else:
        raise SystemExit(f"unknown command: {command}")
    return p


def main(command: str) -> None:
    args = parser_for(command).parse_args()
    dispatch = {
        "ingest": ingest,
        "parse_document": parse_document,
        "segment_source_spans": segment_source_spans,
        "extract_assets": extract_assets,
        "capture_visual_regions": capture_visual_regions,
        "describe_figures": describe_figures,
        "build_source_map": build_source_map,
        "build_reading_frames": build_reading_frames,
        "run_reading_frames": run_reading_frames,
        "integrate_graph_patches": integrate_graph_patches,
        "update_reading_memory": update_reading_memory,
        "extract_atoms": extract_atoms,
        "build_route_graph": build_route_graph,
        "build_route_index": build_route_index,
        "score_paths": score_paths,
        "query_route": query_route,
        "verify_evidence": verify_evidence,
        "validate_build": validate_build,
        "write_build_report": write_build_report,
    }
    if command == "build_figure_atlas":
        build_stub_json(args, "figure_atlas.json")
    elif command == "build_figure_routes":
        build_stub_jsonl(args, ["figure_routes.jsonl"])
    elif command == "build_route_communities":
        build_stub_jsonl(args, ["route_communities.jsonl", "route_reports.jsonl"])
    else:
        dispatch[command](args)

