# Failure Modes

Forbidden behavior:

- treating chunks as knowledge nodes
- summarizing instead of preserving evidence
- building ungrounded graph edges
- using semantic payload, rolling gist, registry summary, or self-explanation as evidence
- answering through top-k spans instead of route paths
- inventing page numbers or bbox coordinates
- silently rewriting a route index during Read Mode
- treating deferred figure artifacts as complete

- running all scripts linearly and treating the result as a completed knowledge network
- using `--mode heuristic-demo` for real builds
- integrating `graph_patch_templates.jsonl` or `reading_frame_packets.jsonl` as if they were actual graph patches