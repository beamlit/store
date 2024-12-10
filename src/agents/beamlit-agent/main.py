import logging
import time
import uuid

from asgi_correlation_id import correlation_id
from fastapi import BackgroundTasks, Request, Response
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# this is dynamically generated, so ignore linting
from agents.beamlit import chains, functions  # type: ignore
from common.bl_config import BL_CONFIG
from common.bl_register_request import handle_chunk, register, send

logger = logging.getLogger(__name__)

global chat_model

chat_model = None


def get_base_url():
    if "agent_model" not in BL_CONFIG:
        raise ValueError("agent_model not found in configuration")
    return f'{BL_CONFIG["run_url"]}/{BL_CONFIG["workspace"]}/models/{BL_CONFIG["agent_model"]["model"]}/v1'


def get_chat_model():
    headers = {
        "X-Beamlit-Authorization": f"Bearer {BL_CONFIG['jwt']}",
        "X-Beamlit-Environment": BL_CONFIG["environment"],
    }
    params = {"environment": BL_CONFIG["environment"]}
    chat_classes = {
        "openai": {"class": ChatOpenAI, "kwargs": {}},
        "anthropic": {"class": ChatAnthropic, "kwargs": {}},
        "mistral": {"class": ChatMistralAI, "kwargs": {"api_key": BL_CONFIG["jwt"]}},
    }
    agent_model = BL_CONFIG["agent_model"]
    provider = agent_model["runtime"]["type"]
    model = agent_model["runtime"]["model"]

    kwargs = {
        "model": model,
        "base_url": get_base_url(),
        "default_query": params,
        "default_headers": headers,
        "api_key": "fake_api_key",
        "temperature": 0,
    }
    chat_class = chat_classes.get(provider)
    if not chat_class:
        logger.warning(
            f"Provider {provider} not currently supported, defaulting to OpenAI"
        )
        chat_class = chat_classes["openai"]
    if "kwargs" in chat_class:
        kwargs.update(chat_class["kwargs"])
    return chat_class["class"](**kwargs)


async def ask_agent(
    body, tools, agent_config, background_tasks: BackgroundTasks, debug=False
):
    global chat_model
    if chat_model is None:
        chat_model = get_chat_model()
        agent_model = BL_CONFIG["agent_model"]
        provider = agent_model["runtime"]["type"]
        model = agent_model["runtime"]["model"]
        logger.info(f"Chat model configured, using: {provider}:{model}")

    # instantiate tools with headers and params
    headers = {
        "x-beamlit-request-id": correlation_id.get() or "",
    }
    if BL_CONFIG.get("jwt"):
        headers["x-beamlit-authorization"] = f"Bearer {BL_CONFIG['jwt']}"
    else:
        headers["x-beamlit-api-key"] = BL_CONFIG["api_key"]
    metadata = {"params": {"debug": str(debug).lower()}, "headers": headers}
    instantiated_tools = [tool(metadata=metadata) for tool in tools]

    memory = MemorySaver()
    use_tools = len(instantiated_tools) > 0
    if use_tools:
        agent = create_react_agent(chat_model, instantiated_tools, checkpointer=memory)
    else:
        agent = chat_model
    all_responses = []
    start = time.time()
    if not use_tools:
        response = agent.invoke(body["input"])
        return [response]

    agent_body = {"messages": [("user", body["input"])]}
    for chunk in agent.stream(agent_body, config=agent_config):
        end = time.time()
        background_tasks.add_task(handle_chunk, chunk, start, end)
        all_responses.append(chunk)
        start = end
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

    debug = request.query_params.get("debug") in ["true", "True", "TRUE"]
    background_tasks.add_task(register, time.time(), debug=debug)
    responses = await ask_agent(
        body, chains + functions, agent_config, background_tasks, debug=debug
    )
    background_tasks.add_task(send, debug=debug)
    if debug:
        return responses
    else:
        content = responses[-1]
        if isinstance(content, AIMessage):
            return Response(
                content=content.content,
                headers={"Content-Type": "text/plain"},
                status_code=200,
            )
        return Response(
            content=content["agent"]["messages"][-1].content,
            headers={"Content-Type": "text/plain"},
            status_code=200,
        )


if __name__ == "__main__":
    main()
