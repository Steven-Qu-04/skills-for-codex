# Reading Context Protocol

Each reading frame should contain local source text, neighbor context, rolling gist, relevant registry slices, recent graph patches, guiding questions, and output schema.

Frame output must be a graph patch. Do not write final `atoms.jsonl` from a reading frame. `integrate_graph_patches.py` creates candidates; `extract_atoms.py` normalizes final atoms.

Rolling gists, concept registries, claim registries, self-explanations, and semantic payloads are navigation memory only. They must not appear as final evidence.

## Manual Frame Reading Procedure

For each `reading_frame_packets.jsonl` row:

1. Read `local_text` and source span metadata.
2. Extract only claims, definitions, distinctions, examples, relations, revisions, and uncertainties actually supported by the frame.
3. Write a graph patch with `reading_frame_id`, `source_span_ids`, `new_atoms`, `candidate_edges`, `concept_terms`, `self_explanation`, and `artifact_status: complete`.
4. Mark empty, ambiguous, cross-reference, or underspecified frames in `repair_suggestions.jsonl` instead of fabricating knowledge.
5. Never continue with placeholder templates as if they were graph patches.