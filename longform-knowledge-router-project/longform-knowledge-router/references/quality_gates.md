# Quality Gates

MVP-0: stable `book.md`, source spans with anchors, no fake bbox values, source coverage report.

MVP-1: atoms grounded to source spans, route nodes and edges grounded, hard/semantic/hypothesis edge classes distinguishable.

MVP-2: reading frame coverage, main source spans read once, graph patches grounded to frames and source spans, route index and path templates exist, Read Mode writes candidate/scored/verified/rejected paths, evidence verification rejects payload-only support.

Mature: visual atlas and figure routes complete, communities and reports route to evidence, advanced ledgers and global synthesis checks pass.

Manual Reading Gate:

- `run_reading_frames.py --mode manual-gate` must stop before graph integration.
- `reading_frame_packets.jsonl` must be read by the AI frame by frame.
- `graph_patches.jsonl` must not contain `execution_mode: heuristic-demo` or `artifact_status: demo_only` for MVP-2 validation.
- `graph_patch_templates.jsonl` is a scaffold, not a build artifact that may be integrated.