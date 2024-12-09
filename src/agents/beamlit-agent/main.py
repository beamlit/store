import logging
import time
import uuid

from asgi_correlation_id import correlation_id
from beamlit.authentication import (get_authentication_headers,
                                    new_client_from_settings)
# this is dynamically generated, so ignore linting
from beamlit.common.settings import get_settings
from fastapi import BackgroundTasks, Request, Response
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from agents.beamlit import chains, functions  # type: ignore

logger = logging.getLogger(__name__)
settings = get_settings()

global chat_model

chat_model = None


def get_base_url():
    return f'{settings.run_url}/{settings.workspace}/models/{settings.agent_model.model}/v1'

def get_chat_model():
    client = new_client_from_settings(settings)

    headers = get_authentication_headers(settings)
    headers["X-Beamlit-Environment"] = settings.environment

    jwt = headers.pop("X-Beamlit-Authorization").replace("Bearer ", "")
    params = {"environment": settings.environment}
    chat_classes = {
        "openai": {
            "class": ChatOpenAI,
            "kwargs": {
                "http_client": client.get_httpx_client()
            }
        },
        "anthropic": {
            "class": ChatAnthropic,
            "kwargs": {}
        },
        "mistral": {
            "class": ChatMistralAI,
            "kwargs": {
                "api_key": jwt
            }
        }
    }

    if settings.agent_model is None:
        raise ValueError("agent_model not found in configuration")
    if settings.agent_model.runtime is None:
        raise ValueError("runtime not found in agent model")
    if settings.agent_model.runtime.type is None:
        raise ValueError("type not found in runtime")
    if settings.agent_model.runtime.model is None:
        raise ValueError("model not found in runtime")

    provider = settings.agent_model.runtime.type
    model = settings.agent_model.runtime.model

    kwargs = {
        "model": model,
        "base_url": get_base_url(),
        "default_query": params,
        "default_headers": headers,
        "api_key": "fake_api_key",
        "temperature": 0
    }
    chat_class = chat_classes.get(provider)
    if not chat_class:
        logger.warning(f"Provider {provider} not currently supported, defaulting to OpenAI")
        chat_class = chat_classes["openai"]
    if "kwargs" in chat_class:
        kwargs.update(chat_class["kwargs"])
    return chat_class["class"](**kwargs)

async def ask_agent(body, tools, agent_config, background_tasks: BackgroundTasks, debug=False):
    global chat_model
    if chat_model is None:
        chat_model = get_chat_model()
        logger.info(f"Chat model configured, using: {settings.agent_model.runtime.type}:{settings.agent_model.runtime.model}")


    # instantiate tools with headers and params
    headers = {
        "x-beamlit-request-id": correlation_id.get() or "",
    }
    metadata = {"params": {"debug": str(debug).lower()}, "headers": headers}
    instantiated_tools = [tool(metadata=metadata) for tool in tools]

    memory = MemorySaver()
    use_tools = len(instantiated_tools) > 0
    if use_tools:
        agent = create_react_agent(chat_model, instantiated_tools, checkpointer=memory)
    else:
        agent = chat_model
    all_responses = []
    if not use_tools:
        response = agent.invoke(body["input"])
        return [response]

    agent_body = {"messages": [("user", body["input"])]}
    for chunk in agent.stream(agent_body, config=agent_config):
        all_responses.append(chunk)
    return all_responses

async def main(request: Request, background_tasks: BackgroundTasks):
    """
        name: langchain-external-providers
        display_name: AI Providers Agent
        description: A chat agent using AI providers like OpenAI, Anthropic, and Mistral to handle your tasks.
        type: agent
        framework: langchain
    """
    sub = request.headers.get("X-Beamlit-Sub", str(uuid.uuid4()))
    agent_config = {"configurable": {"thread_id": sub}}
    body = await request.json()
    if body.get("inputs"):
        body["input"] = body["inputs"]

    debug = request.query_params.get('debug') in ["true", "True", "TRUE"]
    responses = await ask_agent(body, chains + functions, agent_config, background_tasks, debug=debug)
    if debug:
        return responses
    else:
        content = responses[-1]
        if isinstance(content, AIMessage):
            return Response(content=content.content, headers={"Content-Type": "text/plain"}, status_code=200)
        return Response(content=content["agent"]["messages"][-1].content, headers={"Content-Type": "text/plain"}, status_code=200)

if __name__ == "__main__":
    main()
