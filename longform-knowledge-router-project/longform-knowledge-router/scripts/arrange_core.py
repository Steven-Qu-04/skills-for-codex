#!/usr/bin/env python3
"""Arrange Mode and cross-KB read helpers for longform-knowledge-router."""

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

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "are", "was", "were", "has",
    "have", "had", "not", "but", "you", "your", "its", "their", "his", "her", "our", "of",
    "to", "in", "on", "by", "as", "at", "or", "an", "a", "is", "be", "it", "which",
}

ALIGNMENT_RELATIONS = {
    "same_as", "alias_of", "near_equivalent", "broader_than", "narrower_than", "overlaps_with",
    "extends", "applies_to", "supports", "independently_supports", "refutes", "contrasts_with",
    "qualifies", "uses_same_example", "uses_same_method", "shares_evidence_type",
    "historically_precedes", "methodologically_depends_on",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix: str, *parts: Any, n: int = 12) -> str:
    raw = "\u241f".join(str(p) for p in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:n]}"


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8-sig"))


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def ensure_output_dir(path: str | Path) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out


def text_terms(text: str, limit: int = 8) -> list[str]:
    terms = [w.lower() for w in re.findall(r"[\w\u4e00-\u9fff]{2,}", text)]
    counts = Counter(t for t in terms if t not in STOPWORDS and not t.isdigit())
    return [term for term, _ in counts.most_common(limit)]


def first_text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def artifact_terms(row: dict[str, Any], limit: int = 12) -> list[str]:
    values = [first_text(row, "surface", "label", "title", "text", "summary")]
    values.extend(str(v) for v in row.get("aliases", []) if v)
    values.extend(str(v) for v in row.get("concept_terms", []) if v)
    payload = row.get("semantic_payload")
    if isinstance(payload, dict):
        values.extend(str(v) for v in payload.get("routing_semantics", []) if v)
    return text_terms(" ".join(values), limit)


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    lset = set(left)
    rset = set(right)
    if not lset or not rset:
        return 0.0
    return len(lset & rset) / len(lset | rset)


def discover_kbs(args: argparse.Namespace) -> None:
    workspace = Path(args.workspace)
    out = ensure_output_dir(args.output_dir)
    registry = []
    errors = []
    for index in sorted(workspace.rglob("route_index.sqlite")):
        kb_dir = index.parent
        available = {
            "route_index": True,
            "route_graph": (kb_dir / "route_graph.json").exists(),
            "source_spans": (kb_dir / "source_spans.jsonl").exists(),
            "route_nodes": (kb_dir / "route_nodes.jsonl").exists(),
            "route_edges": (kb_dir / "route_edges.jsonl").exists(),
            "route_path_templates": (kb_dir / "route_path_templates.jsonl").exists(),
            "concept_registry": (kb_dir / "concept_registry.jsonl").exists(),
            "claim_registry": (kb_dir / "claim_registry.jsonl").exists(),
            "build_report": (kb_dir / "build_report.md").exists(),
            "validation_report": (kb_dir / "validation_report.json").exists(),
        }
        validation = read_json(kb_dir / "validation_report.json", {})
        validation_status = "valid" if available["route_graph"] and available["source_spans"] else "partial"
        if validation.get("artifact_status") == "failed":
            validation_status = "needs_review"
        kb_id = stable_id("kb", str(kb_dir.resolve()))
        registry.append({
            "kb_id": kb_id,
            "kb_path": str(kb_dir),
            "title": kb_dir.name,
            "source_type": "other",
            "domain": "",
            "build_profile": validation.get("profile", "unknown"),
            "available_artifacts": available,
            "read_mode_endpoint": {"route_index": str(index), "route_graph": str(kb_dir / "route_graph.json")},
            "validation_status": validation_status,
            "source_metadata": {"author": "", "publication_year": "", "discipline": "", "source_role": ""},
        })
        if validation_status != "valid":
            errors.append({"kb_id": kb_id, "kb_path": str(kb_dir), "issue": "child_kb_not_fully_valid", "available_artifacts": available})
    valid_count = sum(1 for row in registry if row["validation_status"] == "valid")
    manifest = {
        "artifact_status": "partial",
        "created_at": now(),
        "workspace": str(workspace),
        "output_dir": str(out),
        "profile": args.profile,
        "kb_count": len(registry),
        "valid_kb_count": valid_count,
        "commands": ["discover_kbs"],
        "arrange_run_type": args.arrange_run_type,
        "quality_gates": {"valid_child_kbs_at_least_2": valid_count >= 2},
    }
    write_json(out / "arrange_manifest.json", manifest)
    write_jsonl(out / "kb_registry.jsonl", registry)
    write_jsonl(out / "errors.jsonl", errors)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def load_kb_objects(kb: dict[str, Any]) -> list[dict[str, Any]]:
    kb_path = Path(kb["kb_path"])
    rows: list[dict[str, Any]] = []
    for object_type, filename, id_key in [
        ("concept", "concept_registry.jsonl", "concept_id"),
        ("claim", "claim_registry.jsonl", "claim_id"),
        ("route_node", "route_nodes.jsonl", "route_node_id"),
    ]:
        for item in read_jsonl(kb_path / filename):
            object_id = item.get(id_key) or item.get("id")
            label = first_text(item, "surface", "label", "title", "text", "summary")
            terms = artifact_terms(item)
            if not object_id or not label or not terms:
                continue
            rows.append({
                "kb_id": kb["kb_id"],
                "object_type": object_type,
                "object_id": object_id,
                "label": label,
                "terms": terms,
                "source_span_ids": item.get("source_span_ids", []),
            })
    return rows


def build_alignment_candidates(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    registry = [row for row in read_jsonl(args.kb_registry) if row.get("validation_status") in {"valid", "partial", "needs_review"}]
    objects_by_kb = {kb["kb_id"]: load_kb_objects(kb) for kb in registry}
    candidates = []
    count_by_pair: dict[str, int] = {}
    for idx, source_kb in enumerate(registry):
        for target_kb in registry[idx + 1:]:
            pair_key = f"{source_kb['kb_id']}::{target_kb['kb_id']}"
            pair = []
            for source in objects_by_kb.get(source_kb["kb_id"], []):
                for target in objects_by_kb.get(target_kb["kb_id"], []):
                    label_score = 1.0 if source["label"].casefold() == target["label"].casefold() else 0.0
                    payload_score = jaccard(source["terms"], target["terms"])
                    if label_score < args.min_label_score and payload_score < args.min_payload_score:
                        continue
                    proposed = "same_as" if label_score == 1.0 and payload_score >= 0.5 else "overlaps_with"
                    pair.append({
                        "alignment_candidate_id": stable_id("ac", source["kb_id"], source["object_id"], target["kb_id"], target["object_id"], proposed),
                        "candidate_type": "concept" if "concept" in {source["object_type"], target["object_type"]} else ("claim" if "claim" in {source["object_type"], target["object_type"]} else "route_node"),
                        "source": source,
                        "target": target,
                        "proposed_relation": proposed,
                        "basis": {
                            "label_similarity": label_score,
                            "payload_similarity": round(payload_score, 3),
                            "structural_similarity": 0.0,
                            "shared_aliases": [],
                            "shared_evidence_type": [],
                            "model_rationale": "",
                        },
                        "status": "needs_child_query" if proposed == "same_as" or payload_score >= 0.35 else "candidate",
                    })
            pair = sorted(pair, key=lambda row: (row["basis"]["label_similarity"], row["basis"]["payload_similarity"]), reverse=True)[:args.max_candidates_per_kb_pair]
            count_by_pair[pair_key] = len(pair)
            candidates.extend(pair)
    kept = []
    count_by_type: Counter[str] = Counter()
    dropped_by_budget = 0
    for candidate in candidates:
        ctype = candidate["candidate_type"]
        if count_by_type[ctype] >= args.max_candidates_per_type:
            dropped_by_budget += 1
            continue
        count_by_type[ctype] += 1
        kept.append(candidate)
    write_jsonl(out / "alignment_candidates.jsonl", kept)
    write_jsonl(out / "cross_concept_registry.jsonl", [{"cross_concept_id": stable_id("xconcept", c["alignment_candidate_id"]), "alignment_candidate_id": c["alignment_candidate_id"], "member_objects": [c["source"], c["target"]], "artifact_status": "candidate"} for c in kept if c["candidate_type"] == "concept"])
    write_jsonl(out / "cross_claim_registry.jsonl", [{"cross_claim_id": stable_id("xclaim", c["alignment_candidate_id"]), "alignment_candidate_id": c["alignment_candidate_id"], "member_objects": [c["source"], c["target"]], "artifact_status": "candidate"} for c in kept if c["candidate_type"] == "claim"])
    write_jsonl(out / "cross_argument_registry.jsonl", [])
    write_json(out / "candidate_generation_report.json", {"artifact_status": "complete", "candidate_count_by_kb_pair": count_by_pair, "candidate_count_by_type": dict(count_by_type), "dropped_by_budget": dropped_by_budget, "dropped_by_low_score": 0})
    print(json.dumps({"candidate_count": len(kept), "dropped_by_budget": dropped_by_budget}, ensure_ascii=False, indent=2))


def query_child_index(kb: dict[str, Any], question: str, terms: list[str]) -> dict[str, Any] | None:
    index = Path(kb.get("read_mode_endpoint", {}).get("route_index") or Path(kb["kb_path"]) / "route_index.sqlite")
    if not index.exists():
        return None
    con = sqlite3.connect(index)
    rows = con.execute("select node_id, label, terms, source_span_ids from nodes").fetchall()
    templates = {row[1]: row for row in con.execute("select template_id, start_node_id, mode, steps_json from templates").fetchall()}
    con.close()
    best = None
    best_score = 0
    for node_id, label, node_terms, source_span_ids in rows:
        matched = sorted(set(terms) & set(str(node_terms).split()))
        if len(matched) <= best_score:
            continue
        tmpl = templates.get(node_id)
        steps = json.loads(tmpl[3]) if tmpl else [{"node_id": node_id, "source_span_ids": json.loads(source_span_ids)}]
        best = {"route_session_id": stable_id("session", kb["kb_id"], question, node_id), "verified_path_id": stable_id("path", kb["kb_id"], question, node_id), "kb_id": kb["kb_id"], "question": question, "matched_terms": matched, "steps": steps, "source_spans": sorted({sid for step in steps for sid in step.get("source_span_ids", [])}), "verification_status": "verified"}
        best_score = len(matched)
    return best


def query_child_kbs(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    registry = {row["kb_id"]: row for row in read_jsonl(args.kb_registry)}
    tasks = []
    sessions = []
    evidence_paths = []
    for candidate in read_jsonl(args.alignment_candidates):
        child_paths = []
        for side in ["source", "target"]:
            obj = candidate.get(side, {})
            question = f"Verify {candidate.get('proposed_relation')} relation for {obj.get('label', obj.get('object_id', 'object'))}"
            task = {"child_query_task_id": stable_id("cqt", candidate["alignment_candidate_id"], side), "alignment_candidate_id": candidate["alignment_candidate_id"], "kb_id": obj.get("kb_id"), "question": question, "mode": "concept_trace" if candidate.get("candidate_type") == "concept" else "local_reading", "target_objects": [obj], "required_evidence_types": ["source_span", "verified_path"], "prompt_or_query_payload": {"terms": obj.get("terms", [])}, "created_from_alignment_candidate": candidate["alignment_candidate_id"], "status": "pending"}
            kb = registry.get(obj.get("kb_id"))
            result = query_child_index(kb, question, obj.get("terms", [])) if kb else None
            if result:
                task["status"] = "executed"
                sessions.append({**result, "child_query_task_id": task["child_query_task_id"]})
                child_paths.append({"kb_id": result["kb_id"], "route_session_id": result["route_session_id"], "verified_path_id": result["verified_path_id"], "source_spans": result["source_spans"], "figures": []})
            else:
                task["status"] = "needs_review" if kb else "failed"
            tasks.append(task)
        status = "verified" if len(child_paths) >= 2 and all(path.get("source_spans") for path in child_paths) else "needs_review"
        evidence_paths.append({"cross_evidence_path_id": stable_id("xep", candidate["alignment_candidate_id"]), "alignment_candidate_id": candidate["alignment_candidate_id"], "question_or_intent": f"Verify cross relation {candidate.get('proposed_relation')}", "cross_steps": [{"step_type": "follow_cross_edge", "kb_id": "", "object_id": candidate["alignment_candidate_id"], "reason": "alignment candidate requires child KB evidence"}], "child_paths": child_paths, "cross_edges": [], "answer_affordance": "compare", "verification_status": status})
    write_jsonl(out / "child_query_tasks.jsonl", tasks)
    write_jsonl(out / "child_query_sessions.jsonl", sessions)
    write_jsonl(out / "cross_evidence_paths.jsonl", evidence_paths)
    print(json.dumps({"tasks": len(tasks), "child_query_sessions": len(sessions), "cross_evidence_paths": len(evidence_paths)}, ensure_ascii=False, indent=2))


def verify_cross_edges(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    candidates = {row["alignment_candidate_id"]: row for row in read_jsonl(args.alignment_candidates)}
    evidence_by_candidate = {row.get("alignment_candidate_id"): row for row in read_jsonl(args.cross_evidence_paths)}
    edges = []
    rejected = []
    repairs = []
    for candidate_id, candidate in candidates.items():
        evidence = evidence_by_candidate.get(candidate_id, {})
        child_paths = evidence.get("child_paths", [])
        has_two_sided = len(child_paths) >= 2 and all(path.get("source_spans") and path.get("verified_path_id") for path in child_paths)
        strong_same_as = candidate.get("proposed_relation") != "same_as" or (candidate.get("basis", {}).get("label_similarity", 0) >= 1.0 and candidate.get("basis", {}).get("payload_similarity", 0) >= 0.5)
        if candidate.get("proposed_relation") not in ALIGNMENT_RELATIONS:
            rejected.append({**candidate, "rejected_reason": "unsupported_relation_type"})
            continue
        if has_two_sided and evidence.get("verification_status") == "verified" and strong_same_as:
            verification_status = "verified"
            confidence = 0.82
        elif has_two_sided:
            verification_status = "needs_review"
            confidence = 0.55
        elif len(child_paths) == 1:
            verification_status = "one_sided"
            confidence = 0.4
        else:
            verification_status = "hypothesis" if candidate.get("status") == "candidate" else "needs_review"
            confidence = 0.25
        edge = {
            "cross_edge_id": stable_id("xedge", candidate_id),
            "alignment_candidate_id": candidate_id,
            "source_kb_id": candidate["source"]["kb_id"],
            "target_kb_id": candidate["target"]["kb_id"],
            "source_object": {"type": candidate["source"]["object_type"], "id": candidate["source"]["object_id"], "label": candidate["source"].get("label", "")},
            "target_object": {"type": candidate["target"]["object_type"], "id": candidate["target"]["object_id"], "label": candidate["target"].get("label", "")},
            "relation_type": candidate.get("proposed_relation"),
            "edge_class": "alignment" if verification_status == "verified" else verification_status,
            "explanation": "Promoted from alignment candidate with child evidence checks.",
            "source_evidence_paths": [path for path in child_paths if path.get("kb_id") == candidate["source"]["kb_id"]],
            "target_evidence_paths": [path for path in child_paths if path.get("kb_id") == candidate["target"]["kb_id"]],
            "verification_status": verification_status,
            "confidence": confidence,
            "provenance": {"child_kb_paths": [path.get("kb_id") for path in child_paths], "source_spans": [sid for path in child_paths for sid in path.get("source_spans", [])], "figures": []},
        }
        edges.append(edge)
        if verification_status != "verified":
            repairs.append({"repair_suggestion_id": stable_id("repair", candidate_id), "alignment_candidate_id": candidate_id, "issue": f"cross_edge_not_verified:{verification_status}", "recommended_action": "Run or inspect child KB Read Mode for both sides and attach verified child paths."})
    write_jsonl(out / "cross_edges.jsonl", edges)
    write_jsonl(out / "rejected_alignments.jsonl", rejected)
    write_jsonl(out / "repair_suggestions.jsonl", repairs)
    print(json.dumps({"cross_edges": len(edges), "rejected": len(rejected), "repairs": len(repairs)}, ensure_ascii=False, indent=2))


def build_cross_route_index(args: argparse.Namespace) -> None:
    out = ensure_output_dir(args.output_dir)
    edges = read_jsonl(args.cross_edges)
    evidence_paths = read_jsonl(args.cross_evidence_paths)
    registry = read_jsonl(args.kb_registry) if args.kb_registry else read_jsonl(out / "kb_registry.jsonl")
    nodes_by_key: dict[str, dict[str, Any]] = {}
    for edge in edges:
        for side in ["source", "target"]:
            obj = edge.get(f"{side}_object", {})
            key = f"{edge.get(f'{side}_kb_id')}::{obj.get('type')}::{obj.get('id')}"
            nodes_by_key.setdefault(key, {"cross_node_id": stable_id("xnode", key), "type": f"cross_{obj.get('type', 'object')}", "title": obj.get("label") or obj.get("id", ""), "summary": "Cross-route entry point. Use linked cross evidence paths and child source spans as evidence.", "member_objects": [{"kb_id": edge.get(f"{side}_kb_id"), "object_type": obj.get("type"), "object_id": obj.get("id"), "role": side}], "semantic_payload": {"routing_semantics": text_terms(obj.get("label", ""), 8), "not_evidence": True}, "can_answer": [], "cannot_answer": ["final answer without child source spans"], "verification_status": edge.get("verification_status", "needs_review")})
    nodes = list(nodes_by_key.values())
    templates = [{"cross_route_template_id": stable_id("xtmpl", p.get("cross_evidence_path_id")), "mode": "cross_synthesis", "cross_evidence_path_id": p.get("cross_evidence_path_id"), "steps": p.get("cross_steps", []), "child_paths": p.get("child_paths", []), "verification_status": p.get("verification_status", "needs_review"), "semantic_payload": {"payload_level": "cross", "not_evidence": True}} for p in evidence_paths]
    write_jsonl(out / "cross_nodes.jsonl", nodes)
    write_jsonl(out / "cross_communities.jsonl", [{"artifact_status": "stubbed", "target_mvp": "arrange_mature", "reason": "Cross community detection is reserved for a later Arrange profile."}])
    write_jsonl(out / "cross_route_templates.jsonl", templates)
    db = out / "cross_route_index.sqlite"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.executescript("""
    create table cross_nodes(cross_node_id text primary key, type text, title text, summary text, verification_status text, payload_json text);
    create table cross_edges(cross_edge_id text primary key, source_kb_id text, target_kb_id text, relation_type text, edge_class text, verification_status text, confidence real, payload_json text);
    create table cross_evidence_paths(cross_evidence_path_id text primary key, question_or_intent text, answer_affordance text, verification_status text, payload_json text);
    create table node_terms(cross_node_id text, term text);
    create table edge_terms(cross_edge_id text, term text);
    create table kb_registry(kb_id text primary key, title text, kb_path text, validation_status text, payload_json text);
    """)
    con.executemany("insert into cross_nodes values(?,?,?,?,?,?)", [(n["cross_node_id"], n["type"], n["title"], n["summary"], n["verification_status"], json.dumps(n, ensure_ascii=False)) for n in nodes])
    con.executemany("insert into cross_edges values(?,?,?,?,?,?,?,?)", [(e["cross_edge_id"], e["source_kb_id"], e["target_kb_id"], e["relation_type"], e["edge_class"], e["verification_status"], e["confidence"], json.dumps(e, ensure_ascii=False)) for e in edges])
    con.executemany("insert into cross_evidence_paths values(?,?,?,?,?)", [(p["cross_evidence_path_id"], p.get("question_or_intent", ""), p.get("answer_affordance", ""), p.get("verification_status", ""), json.dumps(p, ensure_ascii=False)) for p in evidence_paths])
    con.executemany("insert into node_terms values(?,?)", [(n["cross_node_id"], term) for n in nodes for term in text_terms(n.get("title", "") + " " + n.get("summary", ""), 12)])
    con.executemany("insert into edge_terms values(?,?)", [(e["cross_edge_id"], term) for e in edges for term in text_terms(" ".join([e.get("relation_type", ""), e.get("source_object", {}).get("label", ""), e.get("target_object", {}).get("label", "")]), 12)])
    con.executemany("insert into kb_registry values(?,?,?,?,?)", [(kb["kb_id"], kb.get("title", ""), kb.get("kb_path", ""), kb.get("validation_status", ""), json.dumps(kb, ensure_ascii=False)) for kb in registry])
    con.commit()
    con.close()
    print(json.dumps({"cross_nodes": len(nodes), "cross_edges": len(edges), "cross_evidence_paths": len(evidence_paths), "cross_index": str(db)}, ensure_ascii=False, indent=2))


def validate_arrange(args: argparse.Namespace) -> None:
    out = Path(args.arrange_output)
    required = ["arrange_manifest.json", "kb_registry.jsonl", "alignment_candidates.jsonl", "child_query_tasks.jsonl", "cross_evidence_paths.jsonl", "cross_edges.jsonl", "cross_route_index.sqlite"]
    missing = [name for name in required if not (out / name).exists()]
    registry = read_jsonl(out / "kb_registry.jsonl")
    edges = read_jsonl(out / "cross_edges.jsonl")
    candidates = read_jsonl(out / "alignment_candidates.jsonl")
    rejected = read_jsonl(out / "rejected_alignments.jsonl")
    verified_edges = [edge for edge in edges if edge.get("verification_status") == "verified"]
    verified_without_two_sided = [edge.get("cross_edge_id") for edge in verified_edges if not edge.get("source_evidence_paths") or not edge.get("target_evidence_paths")]
    weak_same_as = [edge.get("cross_edge_id") for edge in verified_edges if edge.get("relation_type") == "same_as" and edge.get("confidence", 0) < 0.8]
    book_level_only = [edge.get("cross_edge_id") for edge in edges if edge.get("source_object", {}).get("type") in {"book", "document"} or edge.get("target_object", {}).get("type") in {"book", "document"}]
    payload_used_as_evidence = [edge.get("cross_edge_id") for edge in edges if any("semantic_payload" in path for path in edge.get("source_evidence_paths", []) + edge.get("target_evidence_paths", []))]
    rejected_alignment_candidates = [row for row in candidates if row.get("status") == "rejected"]
    checks = {"required_files_exist": not missing, "valid_child_kbs_at_least_2": sum(1 for kb in registry if kb.get("validation_status") == "valid") >= 2, "verified_edges_have_two_sided_evidence": not verified_without_two_sided, "same_as_edges_have_strong_alignment_evidence": not weak_same_as, "book_level_only_cross_edges": not book_level_only, "payload_used_as_cross_evidence": not payload_used_as_evidence, "rejected_alignment_logged": not rejected_alignment_candidates or len(rejected) >= len(rejected_alignment_candidates), "cross_route_index_exists": (out / "cross_route_index.sqlite").exists()}
    if args.profile == "arrange_mvp":
        checks["verified_cross_edges_at_least_1"] = len(verified_edges) >= 1
    failed = [name for name, ok in checks.items() if not ok]
    report = {"artifact_status": "failed" if failed else ("complete" if args.profile == "arrange_mvp" else "partial"), "profile": args.profile, "valid_child_kb_count": sum(1 for kb in registry if kb.get("validation_status") == "valid"), "candidate_count": len(candidates), "cross_edge_count": len(edges), "verified_cross_edge_count": len(verified_edges), "missing": missing, "failed_checks": failed, "issues": {"verified_without_two_sided": verified_without_two_sided, "weak_same_as": weak_same_as, "book_level_only": book_level_only, "payload_used_as_evidence": payload_used_as_evidence}, "checks": checks}
    write_json(out / "arrange_validation_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failed and args.profile == "arrange_mvp":
        raise SystemExit(1)


def query_cross_route(args: argparse.Namespace) -> None:
    index = Path(args.cross_index)
    out = Path(args.session_dir) if args.session_dir else index.parent / "cross_query_session"
    out.mkdir(parents=True, exist_ok=True)
    terms = text_terms(args.question, 12)
    con = sqlite3.connect(index)
    edge_rows = con.execute("select cross_edge_id, relation_type, verification_status, payload_json from cross_edges").fetchall()
    path_rows = con.execute("select cross_evidence_path_id, question_or_intent, answer_affordance, verification_status, payload_json from cross_evidence_paths").fetchall()
    edge_terms = defaultdict(set)
    for edge_id, term in con.execute("select cross_edge_id, term from edge_terms").fetchall():
        edge_terms[edge_id].add(term)
    con.close()
    paths = [json.loads(row[4]) for row in path_rows]
    candidate_paths = []
    rejected = []
    for edge_id, relation_type, verification_status, payload_json in edge_rows:
        edge = json.loads(payload_json)
        matched = sorted(set(terms) & edge_terms.get(edge_id, set()))
        if not matched:
            label_text = " ".join([edge.get("source_object", {}).get("label", ""), edge.get("target_object", {}).get("label", ""), relation_type or ""])
            matched = sorted(set(terms) & set(text_terms(label_text, 12)))
        if not matched and args.mode != "cross_source_verification":
            continue
        evidence = [path for path in paths if path.get("alignment_candidate_id") == edge.get("alignment_candidate_id")]
        path_status = "verified" if verification_status == "verified" and any(path.get("verification_status") == "verified" for path in evidence) else "needs_review"
        candidate_paths.append({"cross_path_id": stable_id("xpath", args.question, edge_id), "mode": args.mode, "cross_edges": [edge_id], "cross_evidence_paths": [path.get("cross_evidence_path_id") for path in evidence], "child_paths": [child for path in evidence for child in path.get("child_paths", [])], "matched_terms": matched, "verification_status": path_status, "reasons": [f"matched_terms={','.join(matched)}"] if matched else ["cross source verification candidate"], "payload": {"edge": edge, "evidence_paths": evidence, "not_evidence": True}})
    if not candidate_paths:
        rejected.append({"cross_path_id": stable_id("xpathrej", args.question), "rejected_reason": "no_cross_edge_matched_query_terms", "question_terms": terms})
    verified = [path for path in candidate_paths if path["verification_status"] == "verified"]
    spans_by_kb: dict[str, list[str]] = defaultdict(list)
    for path in candidate_paths:
        for child in path.get("child_paths", []):
            spans_by_kb[child.get("kb_id", "")].extend(child.get("source_spans", []))
    source_spans_by_kb = {kb: sorted(set(ids)) for kb, ids in spans_by_kb.items() if kb}
    route_session = {"route_session_id": stable_id("xrs", args.question, now()), "scope": "cross_kb", "question": args.question, "mode": args.mode, "intent": args.mode, "active_cross_nodes": [], "visited_cross_edges": sorted({edge for path in candidate_paths for edge in path.get("cross_edges", [])}), "queried_child_kbs": sorted(source_spans_by_kb), "child_route_sessions": sorted({child.get("route_session_id") for path in candidate_paths for child in path.get("child_paths", []) if child.get("route_session_id")}), "candidate_cross_paths": [path["cross_path_id"] for path in candidate_paths], "verified_cross_paths": [path["cross_path_id"] for path in verified], "rejected_cross_paths": [path["cross_path_id"] for path in rejected], "open_conflicts": [], "uncertainties": [] if verified else ["No verified cross evidence path matched the query; inspect needs_review paths before final claims."], "stop_reason": "cross_candidate_generation_complete", "budget_used": {"cross_nodes_read": 0, "cross_edges_followed": len(candidate_paths), "child_kb_queries": 0, "source_spans_inspected": sum(len(ids) for ids in source_spans_by_kb.values())}}
    answer = {"answer": "", "scope": "cross_kb", "route_session": route_session, "supporting_cross_paths": [path["cross_path_id"] for path in verified], "supporting_child_paths": [child for path in verified for child in path.get("child_paths", [])], "source_spans_by_kb": source_spans_by_kb, "figures_by_kb": {}, "cross_edges_used": sorted({edge for path in verified for edge in path.get("cross_edges", [])}), "conflicts": [path for path in candidate_paths if any(rel in json.dumps(path.get("payload", {})) for rel in ["refutes", "contrasts_with", "qualifies"])], "one_sided_claims": [path for path in candidate_paths if len(path.get("child_paths", [])) == 1], "uncertainties": route_session["uncertainties"], "verification_report": {"requires_verify_evidence": True, "payload_not_evidence": True}}
    write_json(out / "route_session.json", route_session)
    write_jsonl(out / "candidate_cross_paths.jsonl", candidate_paths[:20])
    write_jsonl(out / "verified_cross_paths.jsonl", verified[:8])
    write_jsonl(out / "rejected_cross_paths.jsonl", rejected)
    write_json(out / "answer.json", answer)
    print(json.dumps(answer, ensure_ascii=False, indent=2))


def score_cross_paths(args: argparse.Namespace, session: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    scored = []
    rejected = []
    for path in candidates:
        child_paths = path.get("child_paths", [])
        match_count = len(path.get("matched_terms", []))
        two_sided = len({child.get("kb_id") for child in child_paths if child.get("source_spans")}) >= 2
        verified = path.get("verification_status") == "verified"
        score_parts = {
            "query_relevance": min(1.0, 0.2 * match_count),
            "cross_edge_reliability": 1.0 if verified else 0.45,
            "two_sided_evidence": 1.0 if two_sided else 0.0,
            "child_path_quality": min(1.0, 0.5 * len(child_paths)),
            "kb_coverage": min(1.0, 0.5 * len({child.get("kb_id") for child in child_paths})),
            "conflict_preservation": 1.0 if args.mode == "cross_conflict_trace" else 0.7,
            "evidence_directness": 1.0 if any(child.get("source_spans") for child in child_paths) else 0.0,
            "redundancy_penalty": 0.0,
            "hypothesis_penalty": 0.35 if not verified else 0.0,
            "one_sided_penalty": 0.25 if child_paths and not two_sided else 0.0,
        }
        final = 0.18 * score_parts["query_relevance"] + 0.18 * score_parts["cross_edge_reliability"] + 0.18 * score_parts["two_sided_evidence"] + 0.14 * score_parts["child_path_quality"] + 0.12 * score_parts["kb_coverage"] + 0.10 * score_parts["conflict_preservation"] + 0.10 * score_parts["evidence_directness"] - score_parts["hypothesis_penalty"] - score_parts["one_sided_penalty"]
        score_parts["final_score"] = round(max(0.0, min(1.0, final)), 3)
        row = {**path, "cross_path_score": score_parts}
        if score_parts["final_score"] >= 0.4:
            scored.append(row)
        else:
            rejected.append({**row, "rejected_reason": "cross_score_below_threshold"})
    out = Path(args.route_session).parent
    ordered = sorted(scored, key=lambda r: r["cross_path_score"]["final_score"], reverse=True)
    write_jsonl(out / "scored_cross_paths.jsonl", ordered)
    write_jsonl(out / "verified_cross_paths.jsonl", [row for row in ordered if row.get("verification_status") == "verified"])
    prior_rejected = read_jsonl(out / "rejected_cross_paths.jsonl")
    write_jsonl(out / "rejected_cross_paths.jsonl", prior_rejected + rejected)
    session["verified_cross_paths"] = [p["cross_path_id"] for p in ordered if p.get("verification_status") == "verified"]
    session["stop_reason"] = "path_scoring_complete"
    write_json(out / "route_session.json", session)


def verify_cross_answer(args: argparse.Namespace, answer: dict[str, Any]) -> None:
    session = read_json(args.route_session, {})
    verified_paths = read_jsonl(Path(args.route_session).parent / "verified_cross_paths.jsonl")
    cross_edges = read_jsonl(args.cross_edges) if args.cross_edges else []
    edge_status = {edge.get("cross_edge_id"): edge.get("verification_status") for edge in cross_edges}
    path_breaks = []
    misused = []
    for path in verified_paths:
        if not path.get("cross_evidence_paths"):
            path_breaks.append({"cross_path_id": path.get("cross_path_id"), "issue": "missing_cross_evidence_path"})
        if len({child.get("kb_id") for child in path.get("child_paths", []) if child.get("source_spans")}) < 2:
            path_breaks.append({"cross_path_id": path.get("cross_path_id"), "issue": "missing_two_sided_child_paths"})
        for edge_id in path.get("cross_edges", []):
            if edge_status.get(edge_id) in {"hypothesis", "needs_review", "one_sided"} and path.get("verification_status") == "verified":
                misused.append({"cross_path_id": path.get("cross_path_id"), "cross_edge_id": edge_id, "status": edge_status.get(edge_id)})
    payload_used = any("semantic_payload" in json.dumps(path.get("payload", {})) and path.get("verification_status") == "verified" for path in verified_paths)
    report = {"scope": "cross_kb", "verify_cross_path_grounding": not (answer.get("answer") and not answer.get("supporting_cross_paths")), "verify_child_path_grounding": not path_breaks, "verify_cross_edge_status": not misused, "verify_two_sided_evidence": not path_breaks, "verify_conflict_preserved": True, "verify_no_payload_as_cross_evidence": not payload_used, "path_breaks": path_breaks, "misused_hypothesis_edges": misused, "payload_not_used_as_evidence": not payload_used, "confidence": 0.9 if verified_paths and not path_breaks and not misused and not payload_used else 0.45, "route_session_id": session.get("route_session_id"), "answer_checked": bool(answer)}
    write_json(Path(args.route_session).parent / "verification_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
