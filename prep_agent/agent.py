import anyio
from claude_agent_sdk import (
    query,
    AssistantMessage,
    ResultMessage,
    ToolUseBlock,
    ClaudeAgentOptions,
)
from prep_agent.tools import brief_server, get_saved_brief
from pathlib import Path
from prep_agent.render import to_markdown, to_pdf
from prep_agent.prompt import build_prompt
from prep_agent.mailer import send_email


async def _run_async(company_url: str, profile_path: str, email: str):
    prompt = build_prompt(company_url, profile_path)

    options = ClaudeAgentOptions(
        allowed_tools=["WebSearch", "WebFetch", "mcp__brief-tools__save_brief"],
        mcp_servers={"brief-tools": brief_server},
        permission_mode="bypassPermissions",
        model="claude-haiku-4-5",
        max_turns=20,
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"🔧 {block.name}")
        elif isinstance(message, ResultMessage):
            print("cost (usd):", message.total_cost_usd)

    brief = get_saved_brief()
    if not brief:
        print("⚠️ No brief saved!")
        return
    Path("output").mkdir(exist_ok=True)
    Path(f"output/brief_{brief.company_name.replace(' ', '_')}.md").write_text(
        to_markdown(brief)
    )  # quick text view
    pdf_path = to_pdf(
        brief, f"output/brief_{brief.company_name.replace(' ', '_')}.pdf"
    )  # the deliverable
    print(
        f"\n✅ wrote output/brief_{brief.company_name.replace(' ', '_')}.md and {pdf_path}"
    )
    if email:
        send_email(email, pdf_path, brief.company_name)
    return brief


def run(company_url: str, profile_path: str = "my_profile.md", email: str = None):
    """Sync entry point — hides the async detail from callers (cli, web, cron)."""
    return anyio.run(_run_async, company_url, profile_path, email)
