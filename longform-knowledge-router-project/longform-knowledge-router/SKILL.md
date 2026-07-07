---
name: longform-knowledge-router
description: Construct and read source-verifiable knowledge routing networks for long-form, image-heavy documents. Use for books, PDFs, EPUBs, DOCX, reports, archives, or document folders when Codex must create anchored Markdown, source spans, figure readings, manual reading packets, grounded graph patches, atomic knowledge units, route graphs, route templates, route indexes, or answer questions through verified route paths instead of top-k chunks. Do not use for short summaries, simple OCR, ordinary format conversion, or ordinary vector RAG.
---

# Longform Knowledge Router

## Purpose

Construct or read a source-verifiable knowledge routing network for long-form documents. Treat the document as a navigable evidence system, not as unordered chunks.

## Core Rules

1. Treat source spans as evidence containers, not knowledge nodes.
2. Extract atoms as the minimum knowledge unit.
3. Return route paths, not unordered top-k source spans.
4. Use summaries, rolling gists, registries, and semantic payloads only as navigation aids.
5. Require source spans for important claims.
6. Separate hard, semantic, and hypothesis edges.
7. Prefer the minimum sufficient evidence set.
8. Always generate a figure atlas during construction. The agent may choose any available vision, OCR, screenshot, PDF-rendering, or asset-extraction toolchain, but the result must be normalized into the atlas contract.
9. Never treat scripts as a substitute for AI frame-by-frame reading.
10. Treat `references/read_agent_atandard.md` as the bundled implementation standard for Reading Execution. If a workspace-level `read_agent_atandard.md` is also present, read it as a project override.
11. Real builds must pass the Deep Reader Agent Gate before graph integration or indexing.

## Mode Decision

Use Construct Mode when the user provides raw long-form source documents and asks to build, convert, extract, map, index, or create a knowledge routing network.

Use Read Mode when the user provides a constructed `output_dir`, `route_index.sqlite`, or route graph and asks to read, query, trace, compare, cite, verify, or answer from it.

If the user provides both raw documents and a question, construct the network first unless a valid existing network is available. Then answer through Read Mode.

## Construct Mode

Read `references/workflow.md`, `references/source_segmentation_policy.md`, `references/graph_model.md`, `references/reading_context_protocol.md`, `references/deep_reading_agent_protocol.md`, and `references/read_agent_atandard.md` before running a construction pipeline. If workspace `read_agent_atandard.md` exists, treat it as a project-specific override. Read `references/vision_reading_protocol.md` when the source contains images, tables, formulas, screenshots, or scanned/visual pages.

Construct Mode has an explicit Manual Reading Gate. Scripts may prepare source spans, reading packets, templates, indexes, and validation reports, but scripts must not replace the AI reading each frame and building knowledge step by step.

### Automated Preparation

Run only the preparation scripts before the gate:

```bash
python scripts/ingest.py --input <file_or_dir> --output-dir <output_dir>
python scripts/parse_document.py --manifest <output_dir>/manifest.json --output-dir <output_dir>
python scripts/segment_source_spans.py --raw-blocks <output_dir>/raw_blocks.jsonl --layout-blocks <output_dir>/layout_blocks.jsonl --output-dir <output_dir>
python scripts/extract_assets.py --layout-blocks <output_dir>/layout_blocks.jsonl --output-dir <output_dir>
python scripts/capture_visual_regions.py --layout-blocks <output_dir>/layout_blocks.jsonl --page-images <output_dir>/page_images --output-dir <output_dir>
python scripts/build_source_map.py --source-span-candidates <output_dir>/source_span_candidates.jsonl --layout-blocks <output_dir>/layout_blocks.jsonl --output-dir <output_dir>
python scripts/describe_figures.py --visual-regions <output_dir>/visual_regions.jsonl --source-spans <output_dir>/source_spans.jsonl --output-dir <output_dir>
python scripts/build_reading_frames.py --source-spans <output_dir>/source_spans.jsonl --layout-blocks <output_dir>/layout_blocks.jsonl --output-dir <output_dir>
python scripts/run_reading_frames.py --reading-frames <output_dir>/reading_frames.jsonl --source-spans <output_dir>/source_spans.jsonl --output-dir <output_dir> --profile mvp2 --mode manual-gate
```

`run_reading_frames.py --mode manual-gate` must stop after writing `reading_frame_packets.jsonl`, `graph_patch_templates.jsonl`, and `manual_reading_required.json`.

### Manual Reading Gate

After the gate, the AI must do the actual reading work:

1. Open `reading_frame_packets.jsonl` as a work queue.
2. Read each packet's `local_text`, source span metadata, structural path, and guiding questions.
3. Decide grounded atoms, concept terms, claim terms, candidate edges, uncertainties, and repair needs.
4. Write real deep-reading v2 artifacts from actual packet reading.
5. Do not copy source text wholesale into atoms.
6. Do not integrate `graph_patch_templates.jsonl` or `reading_frame_packets.jsonl` as if they were graph patches.
7. Do not continue until every required frame has a grounded graph patch or an explicit repair suggestion.
8. Use `--mode heuristic-demo` only for smoke tests. MVP-2 validation rejects heuristic demo patches.

### Deep Reader Agent Gate

Real builds must pass this gate before graph integration or indexing. Default mode is `multi-agent-required`.

```bash
python scripts/create_deep_reader_agent.py --output-dir <output_dir> --agent-dir <agent_dir> --batch-size 20 --mode multi-agent-required
```

The main agent must use available worker/sub-agent capability to assign non-overlapping frame batches from `<agent_dir>/BATCH_MANIFEST.json`. Each worker must follow `references/deep_reading_agent_protocol.md`, `references/read_agent_atandard.md`, and any workspace-level `read_agent_atandard.md` override when present.

Workers write or shard these v2 artifacts: `graph_patches.v2.jsonl`, `rolling_gists.v2.jsonl`, `registry_updates.v2.jsonl`, `concept_registry.v2.jsonl`, `claim_registry.v2.jsonl`, `open_reference_ledger.v2.jsonl`, `revision_ledger.v2.jsonl`, `repair_suggestions.v2.jsonl`, and `main_read_status.v2.jsonl`.

If no worker/sub-agent capability is available in `multi-agent-required` mode, mark the build as blocked or incomplete. Do not claim real full-text reading. In `multi-agent-preferred` or `single-agent` mode, a single agent may process all batches but must still satisfy the same deep-reading validation.

Validate and promote only after every frame has a deep-read patch or explicit repair:

```bash
python scripts/validate_deep_reading.py --output-dir <output_dir>
python scripts/promote_deep_reading.py --output-dir <output_dir>
```

### Integration After Reading

Continue only after the Deep Reader Agent Gate is satisfied and v2 artifacts have been promoted:

```bash
python scripts/integrate_graph_patches.py --graph-patches <output_dir>/graph_patches.jsonl --source-spans <output_dir>/source_spans.jsonl --output-dir <output_dir>
python scripts/update_reading_memory.py --graph-patches <output_dir>/graph_patches.jsonl --rolling-gists <output_dir>/rolling_gists.jsonl --output-dir <output_dir>
python scripts/extract_atoms.py --atom-candidates <output_dir>/atom_candidates.jsonl --figure-atom-candidates <output_dir>/figure_atom_candidates.jsonl --source-spans <output_dir>/source_spans.jsonl --output-dir <output_dir>
python scripts/build_route_graph.py --atoms <output_dir>/atoms.jsonl --source-spans <output_dir>/source_spans.jsonl --output-dir <output_dir>
python scripts/build_route_index.py --route-graph <output_dir>/route_graph.json --output-dir <output_dir>
python scripts/build_figure_atlas.py --figure-readings <output_dir>/figure_readings.jsonl --route-nodes <output_dir>/route_nodes.jsonl --output-dir <output_dir>
python scripts/build_figure_routes.py --figure-atlas <output_dir>/figure_atlas.json --route-graph <output_dir>/route_graph.json --output-dir <output_dir>
python scripts/build_route_communities.py --route-graph <output_dir>/route_graph.json --atoms <output_dir>/atoms.jsonl --output-dir <output_dir>
python scripts/write_build_report.py --output-dir <output_dir> --profile mvp2
python scripts/validate_build.py --output-dir <output_dir> --profile mvp2
```

Construct Mode must not answer substantive reading questions from raw documents before the network is constructed unless the user explicitly asks for an ad hoc read.

## Read Mode

Read `references/routing_protocol.md` and `references/route_scoring.md` before querying. Use route traversal and evidence verification; do not rescan the whole raw document as a substitute for the route network.

```bash
python scripts/query_route.py --question "<question>" --index <output_dir>/route_index.sqlite --mode local_reading --strategy explicit_path --session-dir <query_session_dir>
python scripts/score_paths.py --route-session <query_session_dir>/route_session.json --candidate-paths <query_session_dir>/candidate_paths.jsonl --mode local_reading
python scripts/verify_evidence.py --answer <query_session_dir>/answer.json --source-spans <output_dir>/source_spans.jsonl --route-session <query_session_dir>/route_session.json
```

Use `local_reading` for local explanation, `source_location_query` for page/source lookup, and `concept_trace` for a basic concept evolution path. If the route graph is missing evidence, write `repair_suggestions.jsonl` rather than silently rewriting the index during Read Mode.

## Resource Map

- `references/workflow.md`: Construct Mode stages, rerun rules, Manual Reading Gate, and MVP-2 boundary.
- `references/source_segmentation_policy.md`: initial segmentation and source span boundary rules.
- `references/graph_model.md`: atom, route node, edge, and mutual index contracts.
- `references/reading_context_protocol.md`: reading packet assembly, manual frame reading, and memory-not-evidence rule.
- `references/deep_reading_agent_protocol.md`: mandatory deep-reader agent gate, reading windows, multi-agent batch protocol, v2 validation, and promotion rules.
- `references/read_agent_atandard.md`: bundled Reading Execution implementation standard used by deep-reader workers.
- `references/routing_protocol.md`: Read Mode session behavior and route modes.
- `references/route_scoring.md`: scoring fields, penalties, and pruning.
- `references/vision_reading_protocol.md`: screenshot capture, contextual figure reading, atlas contract, figure routes, and AI-selected tool policy.
- `references/evaluation_protocol.md`: fixture expectations and verification layers.
- `references/quality_gates.md`: acceptance metrics.
- `references/failure_modes.md`: forbidden behavior.
- `references/schemas/`: JSON schema contracts for key artifacts.
- `references/prompts/`: prompt contracts for model-assisted stages.
- `scripts/`: deterministic preparation, deep-reader agent setup/validation/promotion, integration, read, validation, scoring, and repair tools.

## Output Contract

Construct Mode MVP-2 outputs must include `book.md`, `assets/`, `source_blocks.jsonl`, `source_span_candidates.jsonl`, `source_spans.jsonl`, `source_segmentation_report.json`, `figures.jsonl`, `tables.jsonl`, `figure_readings.jsonl`, `figure_atom_candidates.jsonl`, `reading_frames.jsonl`, `reading_frame_packets.jsonl`, `graph_patches.jsonl`, `rolling_gists.jsonl`, `concept_registry.jsonl`, `claim_registry.jsonl`, `main_read_status.jsonl`, `atom_candidates.jsonl`, `atoms.jsonl`, `route_nodes.jsonl`, `route_edges.jsonl`, `route_path_templates.jsonl`, `route_graph.json`, `route_index.sqlite`, `repair_suggestions.jsonl`, `build_report.md`, and `errors.jsonl`.

`figure_atlas.json` is mandatory for MVP-2 and must be generated with `artifact_status: "complete"` even when individual figure readings remain uncertain or asset capture is partial. For MVP-2, `figure_routes.jsonl`, `route_communities.jsonl`, and `route_reports.jsonl` may be `stubbed` or `deferred`; mature profile requires `complete`. Each reserved artifact must declare `artifact_status`, `target_mvp`, and `reason` when it is not complete.

## Validation

Run `scripts/validate_deep_reading.py --output-dir <output_dir>` before promoting v2 deep-reading files. Then run `scripts/validate_build.py --output-dir <output_dir> --profile mvp2` before reporting a build as complete. Validate provenance, source-span legality, reading-frame coverage, main-read-once behavior, graph patch grounding, route explainability, verified/rejected path schema, payload-not-evidence, and absence of `heuristic-demo` patches.

When the skill-creator package is available, run its `scripts/quick_validate.py` against this skill folder after editing the skill itself. This is an external authoring convenience, not a runtime dependency.


