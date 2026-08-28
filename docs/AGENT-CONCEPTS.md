# AI Agents — Concepts Reference

*Everything I learned building this agent, written to be reusable for any future agent (not tied to this project). Built on the Claude Agent SDK, but the ideas are general.*

---

## 1. What an AI agent is (vs a plain LLM call)
- **Plain LLM call:** one prompt in, one text answer out. It can only use its training data — it can't reach a database or the live web. It can't *act*.
- **AI agent:** an LLM in a **loop**, given **tools** it can call to take actions, running until the task is done. The model decides which tool to call, sees the result, and decides the next step.

```
LLM reads task → decides: call a tool? → tool runs → result fed back → repeat → final answer
```
> One-liner: *"An agent is an LLM in a loop with tools — it can take actions (query a DB, search the web) and decide the next step from the result. A plain call can't act; the agent can."*

## 2. The Claude Agent SDK — the pieces
The SDK runs the agent loop for you (so you don't hand-write "call model → run tool → feed back").
- **`query(prompt, options)`** — simplest entry; send one prompt, stream back messages.
- **`ClaudeSDKClient`** — a longer-lived client for multi-message sessions.
- **`ClaudeAgentOptions`** — the session config: `allowed_tools`, `mcp_servers`, `permission_mode`, `model`, `max_turns`, `system_prompt`.
- Agents are **async** (they do network I/O) — drive with `anyio.run(main)`; consume the stream with `async for message in query(...)`.

## 3. The message stream (why a stream, why multiple types)
`query()` returns a **stream** of message objects, not one string — because an agent is a **sequence of steps**, not a single reply. Loop it with `async for`.
- **`AssistantMessage`** — content: what the model said/did. Its `.content` is a list of blocks:
  - `TextBlock` — plain text.
  - `ToolUseBlock` — the model calling a tool (the loop, made visible).
- **`ResultMessage`** — the final receipt: token usage + cost, once per run.
> Content vs receipt = two types. One step or a hundred, same loop.

## 4. Tools & MCP (custom capabilities)
- A **tool** = a function you expose to the model; it's the bridge to the DB/web. The model calls it by name when it decides to.
- **MCP (Model Context Protocol)** = a standard for giving a model tools. "Custom MCP tools" = tools you wrote.
- **`@tool(name, description, input_schema)`** — registers a function as a tool. The **description tells the model *when* to use it**; the **schema tells it *what to send*.**
- **`create_sdk_mcp_server(name, tools=[...])`** — bundles your tools into an in-process server.
- Wire in options: `mcp_servers={"my-tools": server}` + `allowed_tools=["mcp__my-tools__my_tool", "WebSearch", "WebFetch"]`. Full tool name = **`mcp__<server>__<tool>`**.
- Built-in tools (`WebSearch`, `WebFetch`) ship with the SDK.

**The inversion to remember:** you *define* the tool but you never *call* it — the **model** does. Your function validates + stashes the data; its **return value goes back to the model**, while the **stashed data goes to your program** (in-process = shared memory).

## 5. Structured output (reliable fields every time)
- Define the output shape as a **Pydantic model**; pass `Model.model_json_schema()` as the tool's `input_schema`. The model fills that "form."
- A `save_*` tool receives the model's args, does `Model(**args)` to **validate**, and stashes the result. If a field is missing/wrong-typed, Pydantic rejects → the agent retries.
- Structured output is the clean handoff: the LLM produces *data*, and rendering (markdown/HTML/PDF) is a plain, cheap, deterministic step with no LLM.

## 6. Loop controls
- **`max_turns`** — a **hard cap** on loop iterations (a runaway/cost guardrail). It's the ceiling, **not** the actual count — if the agent finishes in 4 turns, only 4 are paid. Not a dedup mechanism.
- **`permission_mode="bypassPermissions"`** — don't pause to ask before each tool call (fine for your own script; gate it in a product).
- **`model="claude-haiku-4-5"`** — pick the model (Haiku = cheap/fast to iterate).

## 7. API vs SDK & "shared token quota"
- **API** = the raw model endpoint; you write the loop and run tools yourself. Max control, max plumbing.
- **SDK** = a wrapper that runs the loop + ships tools, **calling the same API underneath**.
- **Shared quota:** SDK or API, every call spends the **same account tokens** and hits the **same rate limits/billing** — one pool.

## 8. Tokens & the context window (the core cost model)
- **Context window = the model's finite "desk"** for one request: system prompt + your input + conversation history + tool results + the output being written. Finite (~200K tokens on most current Claude models).
- **The model is stateless** — it remembers nothing between calls. Each turn, the **whole desk is re-sent**. In an agent loop, history **accumulates** and is re-sent every turn.
- **Input tokens** = the whole context sent that call. **Output tokens** = what the model writes.
- **Cost ≈ context size × number of turns** (because the context is re-sent per turn). The turn count is *actual* turns taken, not `max_turns`.
- Reduce cost two ways that **compound**: (a) **smaller context per turn** (pre-filter), (b) **fewer turns** (efficient design).

## 9. What breaks when the desk gets too full
Four *distinct* failures:
1. **Cost** — input tokens re-sent every turn.
2. **Latency** — more tokens = slower.
3. **Overflow** — exceed the window → hard error or silent truncation (the model can't see part of your data).
4. **Accuracy ("context rot")** — even within the limit, more data = worse answers. Attention dilutes; the model **misses facts in the middle** ("lost in the middle") and gets distracted.
> Bigger context ≠ better — often worse. Goal: the **minimal right** things on the desk. Put instructions + key data at the **edges** (start/end), not buried in the middle.

## 10. Context engineering — best practices
**A. Put less on the desk (retrieve, don't dump):**
- **Pre-filter / retrieve** the relevant slice — deterministic filters (cheap code) or **RAG** (embed data in a vector DB, fetch top-k relevant chunks at query time).
- **Summarize / compact** documents and old history before feeding.
- **Extract only needed fields** from big tool results.

**B. Process huge data in pieces:**
- **Chunking + map-reduce** — split, process each chunk, combine.
- **Sub-agents / fan-out** — each gets a fresh small desk for one slice; a coordinator merges.
- **Pagination / iteration** in bounded batches.

**C. Manage the loop:**
- **Prune tool results** — return summaries, not giant raw blobs.
- **Compaction** — summarize older turns, drop the raw.
- **Bound it** — `max_turns`, tool-result size caps.

**D. Output side:**
- Output also costs and is **capped**. Prefer **structured output**, generate **section-by-section**, or write to a tool/file incrementally rather than one giant message.

> Mantra: **fewer, better tokens beat more tokens.** The skill = "retrieve the relevant slice, keep the desk small."

## 11. Prompt caching
- **Mechanism (API level):** mark a **cache breakpoint** with `cache_control: {"type": "ephemeral"}`; the provider caches everything from the start **up to that point** (the stable prefix). Next call within the TTL with the same prefix reads from cache — **cache reads cost ~10%** and are faster.
- **Put stable stuff first** (system prompt, tools, big docs), **variable stuff last** — if the front changes, the cache misses.
- **TTL:** ~**5 min** default; ~**1 hour** extended option. **TTL is NOT model-dependent.**
- **Cache write** costs a bit more; **reads** are the ~90% saving → pays off with reuse (agent loops, repeated calls).
- **In the Agent SDK it's automatic** — the SDK caches the system prompt + tools + history across the loop. You write no key/code. (That's why input tokens often show up mostly as `cache_read_input_tokens` in `ResultMessage.usage`.)
- **Configurability:** TTL + breakpoints are tunable at the **raw API**; the **high-level SDK does not expose TTL knobs** — drop to the Messages API if you need control.
- **What you control in the SDK:** keep the front of the context **stable** so the cache keeps hitting.

## 12. Per-model values (verify in docs)
| | Varies by model? | Value |
|---|---|---|
| Cache **TTL** | ❌ No | ~5 min default / ~1 hr extended |
| Cache **min prompt size** | ✅ Yes | Haiku higher (~2048 tokens) vs Sonnet/Opus (~1024) |
| **Context window** | ✅ Yes | ~200K standard; Sonnet 1M (beta, tier-gated) |

Exact current numbers (esp. newest models, output limits) change — confirm at **docs.anthropic.com/en/docs/about-claude/models**. In interviews: *"around 200K, I'd confirm the exact figure in the model docs."*

## 13. Design patterns (from two real agents)
Two agents I built illustrate the patterns:
- **A matcher** (maps client plan names → our canonical plans via semantic matching + web research).
- **A coverage agent** (reconciles a region's landscape against our indexed data to surface gaps).

Patterns worth reusing:
- **Guardrail in code, not just prompt.** The prompt is a *request*; a `save_*` tool that **validates against the DB and rejects unreal values** is the *guarantee*. *"The prompt is a request; the code is the guarantee."*
- **Precision over recall / return N/A.** When unsure, return "N/A" rather than guess — a wrong answer is worse than none.
- **Confidence + human loop.** Model emits confidence; high/medium is trusted (and cached), low goes to human review. But **self-reported confidence is circular** — trust it only after **calibrating against a human-labeled sample** (does "High" really = high accuracy?). Add an **independent verifier / self-consistency** check for more trust.
- **Never cache a "no match."** Coverage grows over time, so a no-match today could match later — caching it would hide the future match.
- **Cheap code narrows, expensive model judges.** Pre-filter ~10K candidates to ~5–30 with deterministic matching *before* the LLM decides. Cheaper **and** more accurate (avoids context dilution). The pre-filter is re-sent every turn, so shrinking it saves cost *per turn*.
- **Evaluation = ground truth.** The real answer to "how do you know it works?" is **measuring against a human-labeled set** (precision per confidence tier), not the model's own reasoning.

## 14. Skills (brief)
- A **skill** = a packaged **playbook** (a folder with `SKILL.md` + optional scripts) that teaches the agent how to do a task. It *instructs*; a **tool** *acts*.
- **Progressive disclosure:** the agent only sees each skill's short `description`, and loads the full `SKILL.md` **only when relevant** — so skills add know-how **without bloating the context**.
- Live in `.claude/skills/`; the agent auto-discovers and pulls one in when its description matches.
> *"A tool is a capability the model invokes; a skill is a playbook it reads — loaded only when relevant, so it scales knowledge without eating context."*

## 15. Interview one-liners (memorize)
- *"An agent is an LLM in a loop with tools — it acts and decides the next step; a plain call can't act."*
- *"The prompt is a request; the code is the guarantee."*
- *"I never cache a no-match, because coverage grows — a no today can be a yes tomorrow."*
- *"Cheap code narrows, the expensive model judges — focused context is cheaper *and* more accurate."*
- *"Cost ≈ context × turns, re-sent every turn because the model is stateless — so I shrink the context and the turn count."*
- *"Self-reported confidence is circular; it only means something once calibrated against a labeled set."*
- *"Prompt caching is automatic in the SDK — it caches the stable prefix; my job is to keep that prefix stable."*
