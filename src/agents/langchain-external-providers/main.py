import logging
import time
import uuid

from asgi_correlation_id import correlation_id
from fastapi import BackgroundTasks, Request, Response
from langchain_anthropic import ChatAnthropic
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from common.bl_config import BL_CONFIG
from common.bl_register_request import handle_chunk, register, send

# this is dynamically generated, so ignore linting
from .beamlit import chains, functions  # type: ignore

logger = logging.getLogger(__name__)

global model

model = None

def get_chat_model():
    if "provider" not in BL_CONFIG:
        raise ValueError("Provider not found in configuration")
    if BL_CONFIG['provider'] == 'openai':
        return ChatOpenAI(model=BL_CONFIG["model"], temperature=0, api_key=BL_CONFIG["openai_api_key"])
    elif BL_CONFIG['provider'] == 'anthropic':
        return ChatAnthropic(model=BL_CONFIG["model"], temperature=0, api_key=BL_CONFIG["anthropic_api_key"])
    elif BL_CONFIG['provider'] == 'mistral':
        return ChatMistralAI(model=BL_CONFIG["model"], temperature=0, api_key=BL_CONFIG["mistral_api_key"])
    else:
        raise ValueError(f"Invalid provider: {BL_CONFIG['provider']}")

async def ask_agent(body, tools, agent_config, background_tasks: BackgroundTasks, debug=False):
    global model
    if model is None:
        model = get_chat_model()
        logger.info(f"Chat model configured, using: {BL_CONFIG['provider']}:{BL_CONFIG['model']}")


    # instantiate tools with headers and params
    headers = {
        "x-beamlit-request-id": correlation_id.get() or "",
    }
    if BL_CONFIG.get('jwt'):
        headers["x-beamlit-authorization"] = f"Bearer {BL_CONFIG['jwt']}"
    else:
        headers["x-beamlit-api-key"] = BL_CONFIG['api_key']
    metadata = {"params": {"debug": str(debug).lower()}, "headers": headers}
    instantiated_tools = [tool(metadata=metadata) for tool in tools]

    memory = MemorySaver()
    agent = create_react_agent(model, instantiated_tools, checkpointer=memory)
    all_responses = []
    start = time.time()
    for chunk in agent.stream({"messages": [("user", body["input"])]}, config=agent_config):
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
        configuration:
        - name: provider
          display_name: Provider
          type: selectbox
          description: The provider to use.
          required: true
          options:
            - label: OpenAI
              value: openai
            - label: Anthropic
              value: anthropic
            - label: Mistral
              value: mistral
        - name: model
          display_name: Model
          type: selectbox
          description: The Model to use.
          required: true
          if: provider !== ''
          options:
            - label: gpt-4o-mini
              if: provider === 'openai'
              value: gpt-4o-mini
            - label: claude-3-5-sonnet-20240620
              if: provider === 'anthropic'
              value: claude-3-5-sonnet-20240620
            - label: mistral-7b-latest
              if: provider === 'mistral'
              value: mistral-7b-latest
        - name: openai_api_key
          display_name: OpenAI API Key
          if: provider === 'openai'
          description: OpenAI API key.
          type: string
          required: true
          secret: true
        - name: anthropic_api_key
          display_name: Anthropic API Key
          if: provider === 'anthropic'
          description: Anthropic API key.
          type: string
          required: true
          secret: true
        - name: mistral_api_key
          display_name: Mistral API Key
          if: provider === 'mistral'
          description: Mistral API key.
          type: string
          required: true
          secret: true

    """
    sub = request.headers.get("X-Beamlit-Sub", str(uuid.uuid4()))
    agent_config = {"configurable": {"thread_id": sub}}
    body = await request.json()
    if body.get("inputs"):
        body["input"] = body["inputs"]

    debug = request.query_params.get('debug') in ["true", "True", "TRUE"]
    background_tasks.add_task(register, time.time(), debug=debug)
    responses = await ask_agent(body, chains + functions, agent_config, background_tasks, debug=debug)
    background_tasks.add_task(send, debug=debug)
    if debug:
        return responses
    else:
        content = responses[-1]["agent"]["messages"][-1].content
        return Response(content=content, headers={"Content-Type": "text/plain"}, status_code=200)

if __name__ == "__main__":
    main()
