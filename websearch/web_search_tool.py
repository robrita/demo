"""Web search tool that wraps the Azure AI Foundry agent with Bing grounding."""

from azure.identity import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.aio import AIProjectClient as AsyncAIProjectClient


ENDPOINT = "https://r0bfoundry.services.ai.azure.com/api/projects/r0bAgents"
AGENT_NAME = "robai"
AGENT_VERSION = "6"

_AGENT_REF_BODY = {
    "agent_reference": {
        "name": AGENT_NAME,
        "version": AGENT_VERSION,
        "type": "agent_reference",
    }
}

# Faster than DefaultAzureCredential — only tries the credential types you actually use.
_credential = ChainedTokenCredential(
    AzureCliCredential(),
    ManagedIdentityCredential(),
)

_project_client = AIProjectClient(
    endpoint=ENDPOINT,
    credential=_credential,
)
_openai_client = _project_client.get_openai_client()

_async_project_client = AsyncAIProjectClient(
    endpoint=ENDPOINT,
    credential=_credential,
)
_async_openai_client = _async_project_client.get_openai_client()


def web_search(query: str) -> str:
    """Search the web for real-time information using Bing grounding.

    Args:
        query: The search query to look up on the web.

    Returns:
        The search result as a text string.
    """
    response = _openai_client.responses.create(
        input=[{"role": "user", "content": query}],
        extra_body=_AGENT_REF_BODY,
    )
    return response.output_text


async def async_web_search(query: str) -> str:
    """Async variant of web_search for use in async frameworks (e.g. langgraph).

    Args:
        query: The search query to look up on the web.

    Returns:
        The search result as a text string.
    """
    response = await _async_openai_client.responses.create(
        input=[{"role": "user", "content": query}],
        extra_body=_AGENT_REF_BODY,
    )
    return response.output_text
