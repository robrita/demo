"""Web search tool that wraps the Azure AI Foundry agent with Bing grounding."""

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


ENDPOINT = "https://r0bfoundry.services.ai.azure.com/api/projects/r0bAgents"
AGENT_NAME = "robai"
AGENT_VERSION = "6"

_project_client = AIProjectClient(
    endpoint=ENDPOINT,
    credential=DefaultAzureCredential(),
)
_openai_client = _project_client.get_openai_client()


def web_search(query: str) -> str:
    """Search the web for real-time information using Bing grounding.

    Args:
        query: The search query to look up on the web.

    Returns:
        The search result as a text string.
    """
    response = _openai_client.responses.create(
        input=[{"role": "user", "content": query}],
        extra_body={
            "agent_reference": {
                "name": AGENT_NAME,
                "version": AGENT_VERSION,
                "type": "agent_reference",
            }
        },
    )
    return response.output_text
