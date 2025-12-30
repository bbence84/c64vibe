import os
import base64
from datetime import datetime
import uuid
import asyncio
from pydantic import BaseModel, Field
import utils.agent_utils as agent_utils
import utils.c64_syntax_checker as c64_syntax_checker
from langchain.agents.middleware import TodoListMiddleware
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage

from tools.agent_state import C64VibeAgentState

from langchain.tools import tool, ToolRuntime
from typing import Annotated, Literal, NotRequired
from langgraph.types import Command
from langchain_core.messages import ToolMessage

from langchain.agents import create_agent

from dotenv import load_dotenv
load_dotenv()

from utils.llm_access import LLMAccessProvider
from tools.agent_state import C64VibeAgentState

llm_access_provider = LLMAccessProvider()
use_openrouter = False


model_provider = os.getenv("AI_MODEL_PROVIDER")
model_name = os.getenv("AI_MODEL_NAME")     
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

use_openrouter = False
if openrouter_api_key != "" and openrouter_api_key is not None:
    use_openrouter = True

llm_access_provider.set_llm_model(model_name_technical=model_name, model_provider=model_provider, use_openrouter=use_openrouter)
model_agent = llm_access_provider.get_llm_model()

model_coder = llm_access_provider.get_llm_model(create_new=True, streaming=False)


@tool("DesingProgramPlan", description="Creates a detailed program plan for a Commodore 64 program based on a description")
def create_program_design_plan(description: str) -> str:
    design_instructions = f""" Create a very simple and short design for:
        {description}
        """
    llm_design_response = model_coder.invoke([{"role": "user", "content": design_instructions}])
    print(f"Design response: {llm_design_response}", flush=True)
    return agent_utils.get_message_content(llm_design_response.content)

@tool("WriteC64CodeDummy", description="Generates C64 BASIC V2.0 source code based on a description")
def create_source_code_dummy(description: str, runtime: ToolRuntime[None, C64VibeAgentState]) -> Command:

    source_code = """10 PRINT "HELLO, WORLD!"
    20 GOTO 10
    """
    print(f"Generated source code: {source_code}", flush=True)
    return Command(update={
        "current_source_code": source_code,
        "messages": [ToolMessage(content=f"Created source code and persisted it in the memory", tool_call_id=runtime.tool_call_id)]
    })
deepagent_middleware = [TodoListMiddleware()]
test_agent = create_agent(
    model=model_agent,
    tools=[
        create_program_design_plan,
        create_source_code_dummy,
    ],
    state_schema=C64VibeAgentState,    
    middleware=deepagent_middleware,
    system_prompt=f"You are an expert C64 game programmer. Use the write_todos tool to keep track of the progress. You can create a program design plan using DesingProgramPlan. Then you can create source code using WriteC64CodeDummy. "
)    

message_start = 'A text based game in Hungarian about the political situation'

agent_config = {"configurable": {"thread_id": str(uuid.uuid4())}, "recursion_limit": 50}


async def main():
#def main():
    async for stream_mode, data  in test_agent.astream(
    #for chunk in test_agent.stream(
         config=agent_config,
         stream_mode=["messages", "updates"],  
         input={"messages": [{"role": "user", "content": message_start}]},
    ):  
        # Works for stream_mode="updates"
        # if stream_mode == "updates":
        #     for step, data in data.items():
        #         print(f"step: {step}")
        #         print(f"content: {data['messages'][-1].content_blocks}")        

        if stream_mode == "messages":
            token, metadata = data
            if isinstance(token, AIMessageChunk):
                print(token.text, end="|", flush=True)


        # if chunk and hasattr(chunk, "content"):
        #     print(agent_utils.get_message_content(chunk.content), flush=True)
        
        
        # if hasattr(chunk, "content") and chunk.content:
        #     if isinstance(chunk.content, list):
        #         for content_block in chunk.content:
        #             if isinstance(content_block, dict):
        #                 block_type = content_block.get("type", "")
        #                 print(f"Block type: {block_type}", flush=True)

        #                 if "tool_use" in block_type:
        #                     print(f"Chunk: {block_type} (id: {content_block.get('id', 'N/A')})")

        #                 elif "result" in block_type.lower():
        #                     print(f"Chunk: ✅ {block_type}")

        # for step, data in chunk.items():
        #     print(f"step:{step}", flush=True)
        #     print(f"content:{data["messages"][-1].content_blocks}", flush=True)
        # if chunk and hasattr(chunk, "content_blocks"):
        #     print(chunk.content_blocks.text, flush=True)
        # if chunk and hasattr(chunk, "content"):
        #     #print(agent_utils.get_message_content(chunk.content))
        #     print(f"Content: {chunk.text}", flush=True)
        # if chunk and hasattr(chunk, "content_blocks"):
        #     print(f"Content blocks: {chunk.content_blocks}", flush=True)        

    # async for event in test_agent.astream_events(
    #     config=agent_config,
    #     input={"messages": [{"role": "user", "content": message_start}]},
    #     version="v1"
    # ):
    #     if event["event"] == "on_chat_model_stream":
    #         chunk = event.get("data", {}).get("chunk")

    #         for tool_call in chunk.tool_calls:
    #             # View tool calls made by the model
    #             print(f"Tool: {tool_call['name']}")
    #             print(f"Args: {tool_call['args']}")            

    #         if chunk and hasattr(chunk, "content"):
    #             #print(agent_utils.get_message_content(chunk.content))
    #             print(f"{event['data']['chunk'].text}")
    #         # if chunk and hasattr(chunk, "content_blocks"):
    #         #     print(f"content: {chunk.content_blocks}")
# if __name__ == "__main__":
#     main()
asyncio.run(main())