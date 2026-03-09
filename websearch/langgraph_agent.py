"""LangGraph agent that answers questions using web search via Bing grounding."""

import asyncio
import os

from azure.identity import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential, get_bearer_token_provider
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain_openai import AzureChatOpenAI
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from web_search_tool import web_search, async_web_search

load_dotenv()


search_web = StructuredTool.from_function(
    func=web_search,
    coroutine=async_web_search,
    name="search_web",
    description=(
        "Search the web for real-time information. Use this tool when you need "
        "up-to-date facts, news, weather, or any information that may not be in "
        "your training data."
    ),
)


# --- LLM setup -----------------------------------------------------------
_credential = ChainedTokenCredential(
    AzureCliCredential(),
    ManagedIdentityCredential(),
)
token_provider = get_bearer_token_provider(
    _credential, "https://cognitiveservices.azure.com/.default"
)
llm = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    azure_ad_token_provider=token_provider,
)
llm_with_tools = llm.bind_tools([search_web])


# --- Graph nodes ----------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a helpful assistant that can search the web for real-time information. "
    "When the user asks a question that requires current data (weather, news, prices, "
    "events, etc.), use the search_web tool to find the answer. "
    "Always cite the source of your information when available."
)


async def assistant(state: MessagesState):
    """Call the LLM, optionally invoking tools."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    return {"messages": [await llm_with_tools.ainvoke(messages)]}


# --- Build the graph ------------------------------------------------------
graph_builder = StateGraph(MessagesState)

graph_builder.add_node("assistant", assistant)
graph_builder.add_node("tools", ToolNode([search_web]))

graph_builder.add_edge(START, "assistant")
graph_builder.add_conditional_edges("assistant", tools_condition)
graph_builder.add_edge("tools", "assistant")

graph = graph_builder.compile()


# --- CLI entry point ------------------------------------------------------
async def main():
    print("LangGraph Web Search Agent (type 'quit' to exit)\n")
    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            break

        result = await graph.ainvoke({"messages": [HumanMessage(content=user_input)]})
        ai_message = result["messages"][-1]
        print(f"\nAssistant: {ai_message.content}\n")


if __name__ == "__main__":
    asyncio.run(main())
