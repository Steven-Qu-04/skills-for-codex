# Graph Model

## Atoms

Atoms are the smallest grounded knowledge units. Each atom must carry `atom_id`, `atom_type`, `text`, `source_span_ids`, and confidence or status metadata.

## Route Nodes

Route nodes organize atoms for navigation. Every route node must point to at least one atom or source span and expose `can_jump_to_source`.

## Route Edges

Use edge classes:

- `hard`: structural or explicit document relationships.
- `semantic`: grounded interpretive relationships with evidence spans.
- `hypothesis`: uncertain relationships; never use as final evidence without qualification.

## Mutual Index

Atom -> source span, node -> atom/source span, edge -> evidence span, and path -> steps/source spans must form a closed trace. Semantic payloads help routing but are not evidence.
