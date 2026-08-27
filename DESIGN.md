# Interview-Prep Agent — Design

*An AI agent that researches a company and produces a personalized interview-prep brief (PDF).*

---

## Problem (one sentence)
**Input:** a company URL (+ my resume/profile). **Output:** a PDF interview-prep brief for that company.

> Half the fields are *comparisons* between the company and me (which of my projects to focus on, my skill matches, what to brush up). So my profile is an input too. Lesson: list outputs first, then work backwards to the inputs they require.

## Scope — MVP vs later (avoid feature creep)
| Core MVP (build now) | Deferred (future scope) |
|---|---|
| What the company does, industry, size | Live job-opening scraping + JD matching |
| Tech stack / skills they likely need | Reviews from Glassdoor/AmbitionBox |
| Which of my projects to focus on | Auto-apply on portal |
| My skill matches + gaps to brush up | Email notifications |
| Questions to ask them | Application tracker |
| Render to PDF | "Useful skills" recommender |

Rule: an MVP does the *core loop* well. Job scraping/reviews are each fragile mini-projects — bolt on later.

## Key decisions
| Decision | Pick | Why |
|---|---|---|
| Agent or plain LLM call? | **Agent** | Needs multi-step web research → tools + a loop |
| API or SDK? | **Claude Agent SDK** | Built-in WebSearch/WebFetch, MCP tools, loop handled |
| One agent or many? | **One** (MVP) | Simpler; split later only if needed |
| Reliable fields? | **Structured output** (Pydantic) | Every field filled, fixed shape, easy to render |
| Model | **Start Haiku**, upgrade if needed | Cheap/fast to iterate; feel the cost/quality tradeoff |
| Output | **Markdown → PDF** | Get content right before fighting PDF rendering |

## Core concepts (reference)
- **API vs SDK:** API = raw model endpoint; you write the loop. SDK = wrapper that runs the agent loop + ships tools, calling the same API underneath.
- **Shared token quota:** SDK or API, every call spends the same account tokens + hits the same rate limits/billing. One pool.
- **Tokens:** each request bills input tokens (everything sent: system prompt + history + tool results) + output tokens (what the model writes). An agent loops, so tokens *accumulate* — the full history is re-sent each turn. Main cost driver.
- **N/A rather than guess:** if the site doesn't state something, the field says "not found" — no hallucination.

## Architecture (MVP)
```
   company URL ─┐
                ├─►  ONE agent (Claude Agent SDK)
   my resume  ─┘        │ tools:
                        │   • WebSearch / WebFetch  (built-in: research)
                        │   • save_brief            (custom MCP tool: structured schema)
                        ▼
                structured brief (Pydantic — every field filled or "N/A")
                        ▼
                render → Markdown → PDF
```

## Build order (one concept per step; runs before moving on)
```
v0  hello-agent     ClaudeSDKClient/query + one prompt → print reply   (SDK basics, tokens)
v1  web research    add WebSearch/WebFetch → summarize a URL           (tools + the agent loop)
v2  structured out  Pydantic schema + save_brief custom tool           (@tool, create_sdk_mcp_server, MCP)
v3  personalize     feed my resume → matches/gaps/questions            (prompt engineering, context)
v4  render PDF       structured brief → markdown → PDF                  (output)
── working model done ──
v5+ future          job openings, reviews, notifications, tracker      (deferred)
```

## Recommended folder structure (grow into it)
```
interview-prep-agent/
├── README.md
├── DESIGN.md              # this file
├── requirements.txt
├── .env.example           # ANTHROPIC_API_KEY= (real .env is gitignored)
├── .gitignore
├── src/prep_agent/
│   ├── __init__.py
│   ├── agent.py           # SDK client + the agent loop
│   ├── tools.py           # custom MCP tools (save_brief)
│   ├── schemas.py         # Pydantic models (the brief)
│   ├── prompts.py         # system prompt
│   └── render.py          # markdown → PDF
├── cli.py                 # entry point
└── output/                # generated PDFs (gitignored)
```
We start with a single `hello_agent.py` at the root (v0) and refactor into `src/prep_agent/` at v2 when it grows — so the structure is felt, not imposed.
