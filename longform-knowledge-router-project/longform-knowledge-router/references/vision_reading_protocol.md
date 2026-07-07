# Vision Reading Protocol

## Principle

Visual interpretation is tool-open and result-constrained. The agent may choose any available method that can faithfully inspect the source: direct image viewing, screenshots, rendered PDF pages, OCR, layout extraction, asset extraction, multimodal model calls, or a combination of these.

## Required Result

Construction must generate `figure_atlas.json`. The atlas is required even when some individual readings remain uncertain, incomplete, or based only on surrounding captions/context.

Each atlas entry should preserve:

- the visual region or figure reading id
- the source span id used for provenance
- the asset path when available
- visible facts separated from contextual interpretation
- inferences separated from directly visible facts
- uncertainties and incomplete-reading status
- related route node ids when available

## Tool Freedom

Do not hard-code one required visual tool in the skill contract. Prefer the best available local or connected capability for the document form:

- extracted raster assets for embedded figures
- page screenshots or PDF renderings for scanned or layout-heavy pages
- OCR for text inside figures, tables, and screenshots
- multimodal visual inspection for diagrams, charts, and complex layouts
- caption/context reading when the image itself cannot be inspected yet

## Evidence Boundary

Figure readings and atlas entries are structured evidence aids, not free-standing proof. Final answers must still cite source spans, verified atoms, or structured extracts. When a visual claim depends on interpretation, record uncertainty instead of hiding it.
