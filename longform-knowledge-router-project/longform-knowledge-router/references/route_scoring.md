# Route Scoring

Score fields: term or intent match, path length, source span coverage, edge class reliability, redundancy, uncertainty and hypothesis penalties, cost and budget pressure.

Local questions prefer short direct paths. Concept traces prefer ordered coverage across structural positions. Reject paths with missing source spans, unsupported edges, or payload-only evidence.

## Cross Path Scoring

Cross paths must score query relevance, cross edge reliability, two-sided evidence, child path quality, KB coverage, conflict preservation, evidence directness, redundancy penalty, hypothesis penalty, one-sided penalty, and final score.

`cross_conflict_trace` preserves `contrasts_with`, `refutes`, and `qualifies` edges. `cross_synthesis` prefers KB coverage and two-sided evidence. `cross_source_verification` prefers the shortest verified child path to source spans.
