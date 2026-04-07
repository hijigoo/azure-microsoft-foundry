import os
import logging

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.agentserver.langgraph import from_langgraph

logger = logging.getLogger(__name__)

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        try:
            deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            _llm = init_chat_model(
                f"azure_openai:{deployment_name}",
                azure_ad_token_provider=token_provider,
            )
        except Exception:
            logger.exception("Failed to initialize LLM")
            raise
    return _llm


SYSTEM_PROMPT = "You are a helpful assistant."


def llm_call(state: MessagesState):
    """Call the LLM with the current messages."""
    response = get_llm().invoke(
        [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    )
    return {"messages": [response]}


def build_agent() -> StateGraph:
    builder = StateGraph(MessagesState)
    builder.add_node("llm_call", llm_call)
    builder.add_edge(START, "llm_call")
    builder.add_edge("llm_call", END)
    return builder.compile()


if __name__ == "__main__":
    try:
        agent = build_agent()
        adapter = from_langgraph(agent)
        adapter.run()
    except Exception:
        logger.exception("Agent encountered an error while running")
        raise
