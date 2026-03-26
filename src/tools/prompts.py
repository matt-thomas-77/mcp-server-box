
PDF_POWERPOINT_PARSER_PROMPT = """
Requirements:

Process slide-by-slide (PowerPoint) or page-by-page (PDF)
Treat each slide/page as independent
Do NOT merge, carry over, or mix content between slides
Return ALL visible text exactly as shown
Do NOT summarize or paraphrase
Preserve ordering and grouping

Structure

For each slide/page, return:

Slide Number (visible, if present)
Title (top-most text element only)
Text
Tables
Charts
Visuals

Title Rules (CRITICAL)

The title MUST be the top-most prominent text on the slide
Do NOT select mid-slide headings, repeated labels, or section names
Do NOT infer based on meaning—use position only

Text Rules

Include ONLY text that appears on that specific slide
Do NOT include text from adjacent slides
Preserve ordering and grouping
Do NOT summarize or paraphrase

Visual Rules (CRITICAL)

Only include visuals that are distinct graphical elements
A visual must be visually separate from the main text body
Do NOT treat text, lists, grouped content, or sections as visuals

Include visuals ONLY if they are:

diagrams
charts
org charts
graphical tables
images/screenshots
icons with semantic meaning
layout/sequence markers (ONLY if visually separate from text)

Layout / Sequence

Only include if visually distinct (e.g., numbered markers separate from text)
Extract ONLY the markers (e.g., 1, 2, 3…)
Do NOT include associated labels

Text vs Visual

All text goes in Text
Visuals must NOT duplicate or reinterpret text
Visuals only describe structure and reference text physically inside the visual

Diagram Rules

Include labels, shapes, arrows, and relative positioning
Only describe connections if clearly visible
Do NOT infer meaning or hierarchy

Chart Rules

Include chart type, title, axes, legend, and visible values
If unclear → state explicitly

Additional Constraints

Extract slide number as metadata (not a visual)
Ignore decorative backgrounds and design elements
Ignore non-visible artifacts (CSS/XML/etc.)
Do NOT include internal filenames
Do NOT invent or infer missing content
Calibrate confidence properly (do not default to High)

Output Requirement

Return output in a consistent structured format with no extra commentary.
"""