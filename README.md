# Interview-Prep Agent

An AI agent that researches a company from its website and generates a **personalized interview-prep brief as a PDF** — what the company does, their likely tech stack, which of *your* projects to highlight, your skill gaps to brush up, and smart questions to ask.

Built on the **[Claude Agent SDK](https://docs.anthropic.com/en/api/agent-sdk)** with custom **MCP** tools, structured output, and web research.

**Input:** a company URL + your resume (PDF). **Output:** a tailored `brief.pdf`.

---

## Example

```bash
python cli.py https://stripe.com
# → output/brief.pdf
```

The brief includes: company summary · industry · size · likely tech stack · skills they want ·
**which of my projects to focus on** · **my matching skills** · **skills to brush up** · questions to ask · sources.

## How it works

```
   company URL ─┐
                ├─►  agent (Claude Agent SDK)
   my resume  ─┘        │  tools:
                        │    • WebSearch / WebFetch  (research the company)
                        │    • save_brief            (custom MCP tool: structured schema)
                        ▼
                CompanyBrief (Pydantic — every field filled or "N/A", never guessed)
                        ▼
                render → HTML + CSS → PDF
```

The agent researches the company and its own resume, then calls a custom `save_brief` tool
whose input schema is a Pydantic model — guaranteeing a fixed, validated shape. Rendering is a
plain, deterministic step (no LLM), so the same structured brief can become Markdown, HTML, or PDF.

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
brew install pango            # native lib WeasyPrint needs for PDF rendering
```

The Claude Agent SDK uses your existing Claude Code auth, or set `ANTHROPIC_API_KEY`
(copy `.env.example` → `.env`).

## Usage

```bash
# 1. Add your resume as my_profile.pdf (see my_profile.example.md for the format)
# 2. Run:
python cli.py <company_url>
python cli.py https://stripe.com my_profile.pdf   # explicit profile path
```

Output lands in `output/brief.pdf` (and `output/brief.md`).

## Project structure

```
interview-prep-agent/
├── cli.py                  # entry point: reads the URL, calls the agent
├── prep_agent/             # the package
│   ├── agent.py            # orchestration: wires tools + prompt + runs the loop
│   ├── prompt.py           # builds the prompt; loads the resume (PDF or text)
│   ├── schemas.py          # CompanyBrief — the output structure
│   ├── tools.py            # save_brief — the custom MCP tool
│   └── render.py           # CompanyBrief → Markdown / HTML / PDF
├── my_profile.pdf          # your resume (gitignored — never committed)
├── my_profile.example.md   # sample profile showing the format
├── requirements.txt
└── DESIGN.md               # scope, decisions, architecture, build order
```

## Tech

Python · Claude Agent SDK · MCP (custom tools) · Pydantic (structured output) ·
pypdf (resume extraction) · WeasyPrint (HTML/CSS → PDF).

## Roadmap

- [ ] Live job-opening discovery + JD matching
- [ ] Company reviews (Glassdoor / AmbitionBox)
- [ ] Email the brief on a schedule
- [ ] Application tracker

## License

MIT — see [LICENSE](LICENSE).
