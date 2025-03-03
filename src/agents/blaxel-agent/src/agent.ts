import {
  getAgent,
  getChatModel,
  getDefaultThread,
  getSettings,
  logger,
  newClient,
  OpenAIVoiceReactAgent,
  wrapAgent,
} from "@blaxel/sdk";
import { HumanMessage } from "@langchain/core/messages";
import { FastifyRequest } from "fastify";
import { v4 as uuidv4 } from "uuid";

type InputType = {
  inputs: string | null;
  input: string | null;
};

const websocketHandler = async (
  ws: WebSocket,
  request: FastifyRequest,
  args: any
) => {
  const { agent, functions } = args;
  logger.info("Websocket connected, request: ", request);

  agent.bindTools(functions);
  await agent.connect(ws, ws.send.bind(ws));
  ws.onclose = () => {
    logger.info("Websocket closed");
  };
};

const requestHandler = async (request: FastifyRequest, args: any) => {
  const { agent } = args;
  const body = (await request.body) as InputType;
  const thread_id = getDefaultThread(request) || uuidv4();
  const input = body.inputs || body.input || "";
  const responses: any[] = [];

  const stream = await agent.stream(
    { messages: [new HumanMessage(input)] },
    { configurable: { thread_id } }
  );

  for await (const chunk of stream) {
    responses.push(chunk);
  }
  const content = responses[responses.length - 1];
  return content.agent.messages[content.agent.messages.length - 1].content;
};

async function runAgent(retry: number = 0) {
  try {
    const settings = await getSettings();
    const client = await newClient();
    const { data: agent } = await getAgent({
      client,
      path: { agentName: settings.name },
    });
    if (!agent) {
      throw new Error("Agent not found");
    }
    const chat = await getChatModel(agent?.spec?.model || "");

    const config = {
      agent: {
        metadata: {
          name: agent?.metadata?.name,
        },
        spec: {
          description: agent?.spec?.description,
          prompt: process.env.BL_PROMPT || agent?.spec?.prompt,
          model: agent?.spec?.model,
          agentChain: agent?.spec?.agentChain,
        },
      },
      remoteFunctions: agent?.spec?.functions,
    };
    if (chat instanceof OpenAIVoiceReactAgent) {
      return wrapAgent(websocketHandler, config);
    }
    return wrapAgent(requestHandler, config);
  } catch (error) {
    if (retry > 10) {
      throw error;
    }
    const stackTrace = error instanceof Error ? error.stack : String(error);
    logger.error(`Error running agent: ${stackTrace}`);
    logger.info(`Retrying agent... Retry number:${retry}`);
    await new Promise((resolve) => setTimeout(resolve, 500));
    return runAgent(retry + 1);
  }
}
export const agent = async () => {
  return runAgent();
};
