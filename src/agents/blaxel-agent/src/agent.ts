import { Agent, blModel, blTools, env, getAgent, logger } from '@blaxel/sdk';
import { streamText } from 'ai';
interface Stream {
  write: (data: string) => void;
  end: () => void;
}

async function getTools(agent: Agent) {
  try {
    return await blTools(agent.spec?.functions || []).ToVercelAI()
  } catch (error) {
    logger.error(error)
    throw new Error(`Error connecting to mcp servers, if the agent was just created, it may need an attached mcp server to be deployed.`)
  }
}

async function getModel(agent: Agent) {
  try {
    return await blModel(agent.spec?.model || "").ToVercelAI()
  } catch (error) {
    logger.error(error)
    throw new Error(`Error connecting to model.`)
  }
}

export default async function agent(input: string, stream: Stream) {
  // @ts-ignore
  const agentName = env.BL_NAME || "";
  let {data:agent} = await getAgent({path:{
    agentName
  }})
  if(!agent) {
    throw new Error(`Agent not found : ${agentName}`)
  }
  let [tools,model] = await Promise.all([
    getTools(agent),
    getModel(agent)
  ])
  let system = agent.spec?.prompt || ""
  
  const response = streamText({
    experimental_telemetry: { isEnabled: true },
    model,
    // @ts-ignore
    tools,
    system,
    messages: [
      { role: 'user', content: input }
    ],
    maxSteps: 5,
  });

  for await (const delta of response.textStream) {
    stream.write(delta);
  }

  stream.end();
}
