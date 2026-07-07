# Longform Knowledge Router

This skill is intended to be portable as a self-contained folder. Copy the `longform-knowledge-router` directory into a Codex skills location or another workspace and keep its internal layout intact.

## Included Runtime Resources

- `SKILL.md`: skill contract and mode selection.
- `references/`: workflow, routing, scoring, graph model, schemas, prompts, and the bundled reading execution standard.
- `references/read_agent_atandard.md`: bundled Reading Execution implementation standard. A workspace-level file with the same name may be used as a project-specific override, but is not required for portability.
- `scripts/`: deterministic preparation, routing, scoring, validation, promotion, and repair scripts.
- `assets/`: templates for output manifests, test queries, and deep-reader agent setup.
- `agents/openai.yaml`: optional agent metadata.

## Python Requirements

Python 3.10+ is recommended.

The scripts are standard-library only except for PDF text extraction:

- `PyMuPDF` provides the `fitz` module used by `parse_document.py` for real PDF parsing.
- Without PyMuPDF, PDF parsing falls back to raw byte decoding and is only useful as a last-resort smoke test.

Install runtime dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Construct Mode

Run commands from this folder so script paths in `SKILL.md` resolve as written:

```bash
python scripts/ingest.py --input <file_or_dir> --output-dir <output_dir>
python scripts/parse_document.py --manifest <output_dir>/manifest.json --output-dir <output_dir>
python scripts/segment_source_spans.py --raw-blocks <output_dir>/raw_blocks.jsonl --layout-blocks <output_dir>/layout_blocks.jsonl --output-dir <output_dir>
python scripts/build_source_map.py --source-span-candidates <output_dir>/source_span_candidates.jsonl --layout-blocks <output_dir>/layout_blocks.jsonl --output-dir <output_dir>
```

For real builds, stop at the Manual Reading Gate, complete deep-reader v2 artifacts, validate, promote, then integrate and index as described in `SKILL.md`.

## Read Mode

For an existing constructed output directory:

```bash
python scripts/query_route.py --question "<question>" --index <output_dir>/route_index.sqlite --mode local_reading --strategy explicit_path --session-dir <query_session_dir>
python scripts/score_paths.py --route-session <query_session_dir>/route_session.json --candidate-paths <query_session_dir>/candidate_paths.jsonl --mode local_reading
python scripts/verify_evidence.py --answer <query_session_dir>/answer.json --source-spans <output_dir>/source_spans.jsonl --route-session <query_session_dir>/route_session.json
```

## External Capabilities

The folder does not depend on files from the original workspace. Real deep reading still depends on an AI agent or worker capability because the skill explicitly forbids replacing frame-by-frame reading with keyword heuristics.

The `skill-creator` `quick_validate.py` script mentioned in `SKILL.md` is an optional authoring-time validator, not a runtime dependency.

