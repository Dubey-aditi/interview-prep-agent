"""
render.py — turn a structured CompanyBrief into output.

No LLM here: the agent already produced clean structured data; rendering is a
plain, deterministic, cheap step. Three renderers, all just walking the same
CompanyBrief object:
  - to_markdown : a quick, readable text view
  - to_html     : a styled HTML page (CSS)
  - to_pdf      : that HTML converted to a nice PDF via WeasyPrint
"""

from pathlib import Path
from html import escape

from .schemas import CompanyBrief  # .schemas since it's in the package


# ===========================================================================
# 1. Markdown — quick text view (no dependencies)
# ===========================================================================
def to_markdown(brief: CompanyBrief) -> str:
    def bullets(items):
        return "\n".join(f"- {x}" for x in items) if items else "- N/A"

    return f"""# Interview Prep — {brief.company_name}

## What they do
{brief.what_they_do}

## Industry
{brief.industry}

## Size
{brief.employee_count}

## Likely tech stack
{bullets(brief.tech_stack)}

## Skills they want
{bullets(brief.likely_skills)}

## Projects I should focus on
{bullets(brief.projects_to_focus)}

## My matching skills
{bullets(brief.my_matching_skills)}

## Skills to brush up
{bullets(brief.skills_to_brush_up)}

## Questions to ask them
{bullets(brief.questions_to_ask)}

## Sources
{bullets(brief.sources)}
"""


# ===========================================================================
# 2. HTML — a styled page. You control the look with plain CSS.
# ===========================================================================
CSS = """
@page { size: A4; margin: 1.8cm; }
body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
       color: #1c1c1c; line-height: 1.5; font-size: 11pt; }
h1 { font-size: 24pt; color: #0b5cad; margin: 0 0 2px; }
.subtitle { color: #666; font-size: 10pt; margin-bottom: 18px; }
h2 { font-size: 13pt; color: #0b5cad; border-bottom: 2px solid #e3edf7;
     padding-bottom: 3px; margin-top: 20px; }
p { margin: 6px 0; }
ul { margin: 6px 0; padding-left: 18px; }
li { margin: 3px 0; }
.chips span { display: inline-block; background: #eef4fb; color: #0b5cad;
              border-radius: 12px; padding: 2px 10px; margin: 2px; font-size: 9.5pt; }
.sources li { font-size: 9pt; color: #555; word-break: break-all; }
.meta { color: #444; font-size: 10pt; margin: 0 0 16px; }
"""


def _ul(items):
    """A bullet list (or N/A). escape() makes any text safe inside HTML."""
    if not items:
        return "<ul><li>N/A</li></ul>"
    return "<ul>" + "".join(f"<li>{escape(str(x))}</li>" for x in items) + "</ul>"


def _chips(items):
    """Little rounded 'chips' — nice for short tags like skills/tech."""
    if not items:
        return "<p>N/A</p>"
    return (
        '<div class="chips">'
        + "".join(f"<span>{escape(str(x))}</span>" for x in items)
        + "</div>"
    )


def to_html(brief: CompanyBrief) -> str:
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><style>{CSS}</style></head>
<body>
<h1>{escape(brief.company_name)}</h1>
<div class="subtitle">Interview Prep Brief</div>
<div class="meta">
    <p><strong>Industry:</strong> {escape(brief.industry)} &nbsp;&middot;&nbsp; <strong>Size:</strong> {escape(brief.employee_count)}</p>
</div>

<h2>What they do</h2>
<p>{escape(brief.what_they_do)}</p>

<h2>Likely tech stack</h2>
{_chips(brief.tech_stack)}

<h2>Skills they want</h2>
{_ul(brief.likely_skills)}

<h2>Projects I should focus on</h2>
{_ul(brief.projects_to_focus)}

<h2>My matching skills</h2>
{_chips(brief.my_matching_skills)}

<h2>Skills to brush up</h2>
{_ul(brief.skills_to_brush_up)}

<h2>Questions to ask them</h2>
{_ul(brief.questions_to_ask)}

<h2>Sources</h2>
<div class="sources">{_ul(brief.sources)}</div>
</body>
</html>"""


# ===========================================================================
# 3. PDF — render the HTML to a PDF with WeasyPrint.
# ===========================================================================
def to_pdf(brief: CompanyBrief, path: str = "output/brief.pdf") -> str:
    # Imported here (not at module top) so the rest of the file still works
    # even if WeasyPrint's native libs aren't installed yet.
    from weasyprint import HTML

    Path(path).parent.mkdir(exist_ok=True)  # ensure output/ exists
    HTML(string=to_html(brief)).write_pdf(path)  # HTML + CSS -> PDF
    return path
