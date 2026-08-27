from claude_agent_sdk import tool, create_sdk_mcp_server
from prep_agent.schemas import CompanyBrief

_saved = {}


@tool(
    "save_brief",
    "Save the final structured company interview-prep brief. Call this exactlyonce, at the end",
    CompanyBrief.model_json_schema(),
)
async def save_brief(args):
    brief = CompanyBrief(**args)
    _saved["brief"] = brief
    return {"content": [{"type": "text", "text": "Brief saved successfully."}]}


def get_saved_brief():
    return _saved.get("brief")


brief_server = create_sdk_mcp_server(
    name="brief-tools", version="1.0.0", tools=[save_brief]
)
