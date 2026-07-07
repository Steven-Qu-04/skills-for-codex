# reading_frame_execution

Read one `reading_frame_packets.jsonl` item and produce a grounded graph patch.

Return only knowledge supported by the packet's source spans. Include `reading_frame_id`, `source_span_ids`, `new_atoms`, `candidate_edges`, `concept_terms`, `self_explanation`, and `artifact_status: complete`. Use `repair_suggestions.jsonl` for ambiguity, missing context, unresolved references, or visual evidence that still needs inspection.

Do not summarize the whole document. Do not copy the packet as an atom. Do not use rolling gists, registries, semantic payloads, or self-explanation as evidence.