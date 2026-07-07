# Source Segmentation Policy

Segment by evidence boundaries: headings, paragraphs, list items, figure/caption blocks, tables and table notes, formulas, footnotes/endnotes, block quotes, margin notes, headers, footers, and page numbers.

Do not split by fixed token windows. Do not merge captions, footnotes, or table notes into ordinary paragraphs. Preserve `source_file`, `page`, `bbox`, `reading_order`, `page_reading_order`, `structural_path`, `markdown_anchor`, `split_reason`, `extraction_confidence`, and `status`.

If bbox or page data is unavailable, write `null` and mark the issue in `source_segmentation_report.json`; never invent coordinates.
