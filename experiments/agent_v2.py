import anyio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)
from prep_agent.tools import brief_server, get_saved_brief


async def main():
    company_url = "https://candorhealth.com"
    prompt = (
        f"Research the company at {company_url} using web search and web fetch. "
        "Find: what they do, industry, approximate employee count, likely tech stack, "
        "and the skills they'd want in a backend/data engineer. "
        "Then call save_brief EXACTLY ONCE with the structured result. "
        "For anything you cannot verify from a source, use 'N/A' — do NOT guess."
    )

    options = ClaudeAgentOptions(
        # note the MCP tool's full name: mcp__<server-name>__<tool-name>
        allowed_tools=["WebSearch", "WebFetch", "mcp__brief-tools__save_brief"],
        mcp_servers={"brief-tools": brief_server},  # register your server
        permission_mode="bypassPermissions",
        model="claude-haiku-4-5",
        max_turns=20,
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"🔧 {block.name}")  # watch it call tools, incl. save_brief
        elif isinstance(message, ResultMessage):
            print("cost (usd):", message.total_cost_usd)

    # After the loop, read what the tool captured -> structured, validated data.
    brief = get_saved_brief()
    print("\n=== STRUCTURED BRIEF ===")
    print(brief.model_dump_json(indent=2) if brief else "⚠️ No brief was saved!")


anyio.run(main)
