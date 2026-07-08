# Routing Protocol

Read Mode starts a `route_session.json` and works through route paths.

Supported MVP-2 modes:

- `local_reading`: answer from direct local evidence paths.
- `source_location_query`: locate pages, anchors, and spans.
- `concept_trace`: trace a concept through route nodes and evidence spans.

Read Mode writes `candidate_paths.jsonl`, `expanded_paths.jsonl`, `verified_paths.jsonl`, `rejected_paths.jsonl`, `answer.json`, and `verification_report.json`.

Do not answer from top-k spans alone. A final answer must cite verified paths and source spans.

## Cross-KB Read Mode

Read Mode supports `single_kb`, `cross_kb`, and `auto` scope. Use `single_kb` for a normal `route_index.sqlite`; use `cross_kb` for an Arrange output with `cross_route_index.sqlite`, `kb_registry.jsonl`, `cross_edges.jsonl`, and `cross_evidence_paths.jsonl`.

Cross-KB modes are `cross_local_reading`, `cross_synthesis`, `cross_concept_trace`, `cross_argument_trace`, `cross_conflict_trace`, `cross_evidence_verification`, and `cross_source_verification`.

A cross answer must route through `cross_evidence_path`, then child verified paths, then child source spans. Cross node summaries, edge explanations, semantic payloads, and route reports are navigation aids only.
