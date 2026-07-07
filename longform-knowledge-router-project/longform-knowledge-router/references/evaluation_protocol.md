# Evaluation Protocol

MVP-2 fixtures should verify local reading returns paths, source location queries return spans, concept traces return ordered route evidence, scoring produces accepted and rejected paths, evidence verification checks atom/edge/path/answer grounding, and payloads/gists/self-explanations are not used as evidence.

Validation should fail on missing required artifacts, duplicate main reads, orphan atoms/nodes, source mismatches, and complete-profile visual artifacts that remain deferred.

Manual gate fixture:

Run a fixture through `run_reading_frames.py --mode manual-gate` and expect non-zero exit, `reading_frame_packets.jsonl`, `graph_patch_templates.jsonl`, `manual_reading_required.json`, and no `graph_patches.jsonl`. Run a separate heuristic demo fixture and expect MVP-2 validation to reject it.