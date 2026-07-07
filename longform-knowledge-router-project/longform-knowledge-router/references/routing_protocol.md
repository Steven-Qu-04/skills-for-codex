# Routing Protocol

Read Mode starts a `route_session.json` and works through route paths.

Supported MVP-2 modes:

- `local_reading`: answer from direct local evidence paths.
- `source_location_query`: locate pages, anchors, and spans.
- `concept_trace`: trace a concept through route nodes and evidence spans.

Read Mode writes `candidate_paths.jsonl`, `expanded_paths.jsonl`, `verified_paths.jsonl`, `rejected_paths.jsonl`, `answer.json`, and `verification_report.json`.

Do not answer from top-k spans alone. A final answer must cite verified paths and source spans.
