import anyio
from claude_agent_sdk import query, AssistantMessage, ResultMessage, TextBlock

# The agent runs asynchronously, so our function is `async` and we drive it
# with anyio.run() at the bottom. (Agents do I/O — network calls — so async.)


async def main():
    prompt = "In 2 sentense explain what AI Agent is."

    # query() = the simplest SDK entry point: send one prompt, stream back messages.
    # It doesn't return a single string — it yields a SEQUENCE of message objects
    # as the agent works. We loop over them and pick out the parts we care about.
    async for message in query(prompt=prompt):
        # AssistantMessage = something the model "said". Its .content is a list of
        # blocks; a TextBlock is plain text. (Later we'll also see ToolUseBlock.)
        if isinstance(message, AssistantMessage):
            print("\n--- assistant ---")
            print(message)

            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        # ResultMessage = the final summary of the whole run: token usage + cost.
        # THIS is where you SEE tokens — the concept you wanted to understand.
        elif isinstance(message, ResultMessage):
            print("\n--- result ---")
            print(message)
            print("\n--- usage ---")
            print("input tokens: ", message.usage.get("input_tokens"))
            print("output tokens:", message.usage.get("output_tokens"))
            print("cost (usd):   ", message.total_cost_usd)


anyio.run(main)
