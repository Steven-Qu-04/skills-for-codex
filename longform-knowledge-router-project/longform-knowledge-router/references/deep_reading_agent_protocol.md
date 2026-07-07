# Deep Reading Agent Protocol

Use this protocol after `run_reading_frames.py --mode manual-gate`. It operationalizes bundled `references/read_agent_atandard.md` as the skill's implementation standard for Reading Execution.

## Authority

`references/read_agent_atandard.md` is the bundled implementation standard for agentic longform reading. A workspace-level `read_agent_atandard.md`, when present, is a project override. If a shortcut would pass schema validation but violates these principles, reject the shortcut:

- Source spans are evidence containers, not knowledge nodes.
- Atoms are the minimum knowledge units.
- Route results are paths, not unordered top-k chunks.
- Important claims require source spans.
- Hard, semantic, and hypothesis edges are separate layers.
- Summaries, registries, rolling gists, semantic payloads, and self-explanations are memory/navigation, not evidence.
- A completed build requires evidence closure: atom -> source span, node -> atom/source span, edge -> evidence span, path -> steps/source spans.

## Deep Reader Agent Gate

After the Manual Reading Gate, create or use a project-specific Deep Reader Agent. In multi-agent-required mode, the main agent must attempt to assign frame batches to worker/sub-agents. If no worker/sub-agent capability is available, mark the build `blocked_deep_reader_agent_unavailable`; do not report a real full-text build.

Allowed modes:

- `multi-agent-required`: default for real builds; fail closed if workers are unavailable.
- `multi-agent-preferred`: use workers when available, otherwise continue as a single deep-reading agent and label the mode.
- `single-agent`: one agent may process all batches, still using the same reading windows and completion gates.

## Reading Window

Each frame must be read through a finite working-memory window:

1. `local_text`: current evidence text; do not compress it away.
2. `source_span_ids` and metadata: page, bbox, anchor, reading order, block type, structural path.
3. Left context summary from 1-3 nearby frames; memory only.
4. Right context preview from 1-2 nearby frames; memory only.
5. Section rolling gist; memory only and `not_evidence: true`.
6. Relevant concept/claim/entity/figure registry slice; do not load the full registry.
7. Recent 3-5 graph patches for continuity.
8. Guiding questions and output schema.

Default context budget:

- `local_text`: 50-60%
- neighbor context: 10-15%
- rolling gist and registry slice: 15-20%
- instructions/schema: 10%
- output reserve: 10%

When over budget, preserve current evidence first, then source metadata, guiding questions, registry slice, recent patches, rolling gist, neighbor summaries, and finally low-relevance historical notes.

## Reading Behavior

For every frame, decide whether it introduces or updates:

- a definition, distinction, claim, premise, evidence, example, conclusion, or limitation
- a process step or method instruction
- a case observation, transformation marker, or outcome
- a cross-reference, unresolved pronoun/reference, contradiction, or revision
- an OCR/layout/figure/table repair need

Do not:

- turn a paragraph summary into an atom
- treat a source span as a route node
- promote front matter, endorsements, or copyright text into clinical/theoretical claims
- use keyword extraction as reading
- write current-frame evidence from rolling memory
- silently overwrite previous atoms, edges, or registry items
- integrate `graph_patch_templates.jsonl` or `reading_frame_packets.jsonl` as actual patches

## Batch Protocol

Process frames in document order, normally in batches of 10-25 frames. Each worker owns a non-overlapping frame range and writes batch-scoped v2 shards or directly appends to v2 JSONL under coordination.

Each batch must update:

- `graph_patches.v2.jsonl`
- `rolling_gists.v2.jsonl`
- `registry_updates.v2.jsonl`
- `repair_suggestions.v2.jsonl`
- `main_read_status.v2.jsonl`
- `DEEP_READING_STATUS.md`

Recommended additional ledgers:

- `concept_registry.v2.jsonl`
- `claim_registry.v2.jsonl`
- `open_reference_ledger.v2.jsonl`
- `revision_ledger.v2.jsonl`

## Graph Patch Requirements

Each complete frame must produce one grounded graph patch with:

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
- `artifact_status: complete`
- `execution_mode: deep-manual-ai-reading`

Frames that cannot be reliably read must write an explicit repair suggestion and a `main_read_status` of `repair_required`.

## Completion Gate

Do not promote v2 files or build the route index until:

- every reading packet has a deep-read patch or explicit repair status
- no atom lacks source spans
- no semantic edge lacks evidence spans
- no `heuristic-demo` or `demo_only` output exists
- rolling gists, registries, payloads, and self-explanations are not used as evidence
- `validate_deep_reading.py` passes

Only after this gate may `promote_deep_reading.py`, `integrate_graph_patches.py`, `extract_atoms.py`, `build_route_graph.py`, `build_route_index.py`, and `validate_build.py` run.

