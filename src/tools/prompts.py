
PDF_POWERPOINT_PARSER_PROMPT = """
Extract high-value structured content from PowerPoint and PDF slide decks.

Your output will be consumed by another LLM agent. Prioritize structure, completeness of meaningful content, and deduplication over verbatim text.

CRITICAL RULES

You are NOT allowed to:

return slide-by-slide output
include slide numbers
perform verbatim extraction
output raw slide text

If you do any of the above, your response is incorrect.

You MUST:

ignore slide boundaries completely
merge and deduplicate content across all slides
transform the document into a normalized knowledge representation

This is NOT extraction. This is transformation.

HARD CONSTRAINTS
Output MUST fit in ONE response (≤ 2500 tokens)
No continuation responses
No redundancy
No filler content
STYLE RULE (CRITICAL)
Use short bullet points only
NO paragraphs
NO long sentences
Minimize words per bullet
Prefer noun phrases over sentences
Be concise and compressed
OBJECTIVE

Extract ALL meaningful content, including:

frameworks and models
processes and workflows
definitions and terminology
metrics and measurement systems
system architecture (roles, tools, components)
relationships between concepts
meaningful visual structures
CORE BEHAVIOR
Deduplicate aggressively (each concept appears once)
Normalize terminology into consistent entities
Preserve exact phrasing ONLY for definitions
Remove repetition and low-value content
Represent information once in its best form
COVERAGE RULE (CRITICAL)

Do NOT omit important frameworks, processes, or systems.

If compression is required:

reduce detail per item
DO NOT reduce number of important concepts
OUTPUT FORMAT (STRICT)

Return EXACTLY these sections:

Document Summary
Canonical Models
Process Library
Metrics & Measurement
Resource / System Architecture
Terminology Mapping
Visual Structure Extraction

Do NOT include any other sections.

SECTION REQUIREMENTS
Document Summary
Purpose
Key Themes
Core Frameworks
Key Entities
Key Relationships
Measurement Systems
Canonical Models (TARGET 5–7, include all important models if present)

For each:
Model Name:
Components:
Definition:
Relationships:
Usage Context:

RULES:

Max 4 bullets total for Definition + Relationships + Usage
Compress wording, not concepts
Process Library (TARGET 5–7, include all important processes if present)

For each:
Process Name:
Stages:
Inputs:
Outputs:
Owners (if stated):

RULES:

Max 5 stages per process
Each stage = 1 short line
Keep all key processes even if compressed
Metrics & Measurement

For each:
Metric Name:
What it measures:
Constraints:
Hierarchy (if any):

RULES:

Include only true metrics (not dashboards/tools)
Keep minimal
Resource / System Architecture
Components (roles, tools, systems)
Categories (if applicable)
How components connect
Terminology Mapping
Term → Definition
Term A → Equivalent Term B
Visual Structure Extraction

For each visual model:
Type: (diagram / flow / hierarchy / system)
Components:
Connections:
Description (structure only)

Do NOT describe styling.

COMPRESSION PRIORITY

If output approaches limit:

Keep Canonical Models
Keep Process Library
Keep Metrics
Reduce detail in other sections
HARD STOP RULE (CRITICAL)

If nearing token limit:

STOP adding detail immediately
Do NOT expand definitions
Do NOT add low-priority content
GOAL

Produce a dense, structured, machine-readable output suitable for:

knowledge graphs
RAG ingestion
cross-document comparison
"""