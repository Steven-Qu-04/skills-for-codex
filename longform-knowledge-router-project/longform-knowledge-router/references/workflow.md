# Workflow

## Construct Mode Stages

1. Ingest source files into `manifest.json`.
2. Parse raw text/layout blocks without claiming knowledge.
3. Segment source spans by evidence boundaries, not fixed token size.
4. Extract visual/table/formula candidates and preserve mappings.
5. Build `book.md` with stable Markdown anchors and `source_spans.jsonl`.
6. Build reading frames from source spans.
7. Run `run_reading_frames.py --mode manual-gate` to emit reading packets and graph patch templates, then stop.
8. The AI reads each packet and writes grounded `graph_patches.jsonl`, `rolling_gists.jsonl`, registries, and repair suggestions. Only then integrate patches into candidates and normalize final atoms.
9. Build route graph, path templates, and SQLite route index.
10. Reserve MVP-3 visual atlas/routes and community/report artifacts with explicit status.
11. Validate with the requested profile before reporting success.

## Rerun Rules

Rerun downstream stages after changing an upstream artifact. If `source_spans.jsonl` changes, rerun reading frames, graph patches, atoms, route graph, route index, and validation.

Construct Mode produces indexes and route templates. It does not produce final answers to user questions.

## MVP-2 Boundary

MVP-2 must implement document provenance, atoms, route graph, route index, reading sessions, scored paths, verified/rejected paths, and repair suggestions. Full figure atlas, figure routes, communities, global synthesis, and advanced ledgers are reserved for MVP-3, but their artifact contracts must remain visible.

## Manual Reading Gate

`run_reading_frames.py` is not a reader in production mode. Its default `manual-gate` mode writes `reading_frame_packets.jsonl`, `graph_patch_templates.jsonl`, and `manual_reading_required.json`, then exits. The agent must inspect each packet and produce grounded graph patches before continuing. `--mode heuristic-demo` is permitted only for smoke tests and must never be accepted as an MVP-2 build.