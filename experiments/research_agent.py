import anyio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)


async def main():
    company_url = "https://candorhealth.com"
    prompt = (
        f"Research the company at {company_url}. "
        "Use web search and web fetch to find: what the company does, its industry, "
        "rough employee count, and the tech stack they likely use. "
        "Then give a short summary."
    )

    # ClaudeAgentOptions = the SESSION CONFIG. In v0 we passed nothing (defaults).
    # Now we configure the agent:
    options = ClaudeAgentOptions(
        allowed_tools=[
            "WebSearch",
            "WebFetch",
        ],  # build-in agent tools we want to allow the agent to use
        permission_mode="bypassPermissions",  # don't pause to ask us before each tool call
        model="claude-haiku-4-5",
        max_turns=15,  # safety cap on loop iterations
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print("💬", block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"🔧 tool call → {block.name}   input={block.input}")
        elif isinstance(message, ResultMessage):
            print("\n--- usage ---")
            print("input tokens: ", message.usage.get("input_tokens"))
            print("output tokens:", message.usage.get("output_tokens"))
            print("cost (usd):   ", message.total_cost_usd)


anyio.run(main)
