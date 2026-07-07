# Deep Reader Agent

## Mission

Deep-read `<output_dir>/reading_frame_packets.jsonl` and produce source-verifiable v2 reading artifacts before any route graph/index is built.

Follow:

- `<skill_dir>/SKILL.md`
- `<skill_dir>/references/deep_reading_agent_protocol.md`
- `<skill_dir>/references/read_agent_atandard.md`
- `<workspace>/read_agent_atandard.md` when available as a project override

## Inputs

- Project output directory: `<output_dir>`
- Reading packets: `<output_dir>/reading_frame_packets.jsonl`
- Source spans: `<output_dir>/source_spans.jsonl`
- Reading frames: `<output_dir>/reading_frames.jsonl`
- Book markdown: `<output_dir>/book.md`
- Batch manifest: `<agent_dir>/BATCH_MANIFEST.json`

## Outputs

Write v2 files first:

- `graph_patches.v2.jsonl`
- `rolling_gists.v2.jsonl`
- `registry_updates.v2.jsonl`
- `concept_registry.v2.jsonl`
- `claim_registry.v2.jsonl`
- `open_reference_ledger.v2.jsonl`
- `revision_ledger.v2.jsonl`
- `repair_suggestions.v2.jsonl`
- `main_read_status.v2.jsonl`
- `DEEP_READING_STATUS.md`

## Rules

1. Read each assigned frame's `local_text`.
2. Do not use `heuristic-demo`.
3. Do not generate patches from keywords alone.
4. Do not treat summaries, registries, semantic payloads, or self-explanations as evidence.
5. Every atom must have `source_span_ids`.
6. Every semantic edge must have `evidence_span_ids`.
7. Mark unreadable or underspecified frames as `repair_required`.
8. Never claim real full-text reading until every frame has a patch or repair status.

## Batch Work

Process only the batch range assigned to you. Write batch-scoped shards when multiple workers are active, or append to v2 files only when the main coordinator has assigned exclusive write access.

For each frame, output a graph patch with:

- `graph_patch_id`
- `reading_frame_id`
- `source_span_ids`
- `new_atoms`
- `candidate_edges`
- `concept_terms`
- `claim_terms`
- `unresolved_references`
- `possible_revisions`
- `self_explanation`
- `artifact_status`
- `execution_mode: deep-manual-ai-reading`

Update `DEEP_READING_STATUS.md` with frames completed, repairs, active concepts, active claims, unresolved references, and next batch.

