#  █████   █████  ███  █████                █████████   ████████  █████ █████ 
# ░░███   ░░███  ░░░  ░░███                ███░░░░░███ ███░░░░███░░███ ░░███  
#  ░███    ░███  ████  ░███████   ██████  ███     ░░░ ░███   ░░░  ░███  ░███ █
#  ░███    ░███ ░░███  ░███░░███ ███░░███░███         ░█████████  ░███████████
#  ░░███   ███   ░███  ░███ ░███░███████ ░███         ░███░░░░███ ░░░░░░░███░█
#   ░░░█████░    ░███  ░███ ░███░███░░░  ░░███     ███░███   ░███       ░███░ 
#     ░░███      █████ ████████ ░░██████  ░░█████████ ░░████████        █████ 
#      ░░░      ░░░░░ ░░░░░░░░   ░░░░░░    ░░░░░░░░░   ░░░░░░░░        ░░░░░                                                                        
# -----------------------------------------------------------
# VibeC64: An AI Agent for Commodore 64 Program Creation
# Created by Bence Blaske - 2026
# -----------------------------------------------------------                                       

import os
import uuid
import asyncio
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent

from langchain.agents.middleware import HumanInTheLoopMiddleware, InterruptOnConfig, TodoListMiddleware
from deepagents.middleware.filesystem import FilesystemMiddleware


from utils.formatting import format_messages, format_message

from tools.agent_state import VibeC64AgentState
from tools.coding_tools import CodingTools
from tools.testing_tools import TestingTools
from tools.game_design_tools import GameDesignTools
from tools.hw_access_tools import HWAccessTools

from rich.prompt import Prompt
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from utils.llm_access import LLMAccessProvider

console = Console()

def load_ai_model_from_env():
    global llm_access_provider
    model_provider = os.getenv("AI_MODEL_PROVIDER")
    model_name = os.getenv("AI_MODEL_NAME") 
    api_key = os.getenv("API_KEY")    

    use_openrouter = False
    if model_provider == "openrouter":
        use_openrouter = True            
    try:
        llm_access_provider.set_llm_model(model_name_technical=model_name, api_key=api_key,model_provider=model_provider, use_openrouter=use_openrouter)
    except Exception as e:
        print(f"Error setting LLM model from env: {e}")        

llm_access_provider = LLMAccessProvider()
load_ai_model_from_env()

model_coder = llm_access_provider.get_llm_model()
model_agent = llm_access_provider.get_llm_model()
model_screen_ocr = llm_access_provider.get_llm_model()

coding_tools = CodingTools(llm_access=llm_access_provider)
testing_tools = TestingTools(llm_access=llm_access_provider)
hw_access_tools = HWAccessTools()
game_design_tools = GameDesignTools(llm_access=llm_access_provider)

vibec64_agent_instructions = f"""
    You are VibeC64, an AI Agent specialized in creating games for the Commodore 64 computer.
    Use the various tools and at your disposal to create, test, and run C64 games.
    When given a user request, first determine if it involves creating or modifying a C64 game.

    Tool use instructions:
    - If code creation or modification is needed, first use the DesignGamePlan tool to create a detailed game design plan 
    - Use the WriteC64BasicCode tool to generate syntactically correct code based on the design plan created by DesignGamePlan. Don't specify code in the description, only the design plan.
    - After generating the code, use the SyntaxChecker tool to ensure there are no synAtax errors.
    - If there are syntax errors, correct them using the FixSyntaxErrors tool and re-check them using the SyntaxChecker tool until the code is error-free.
    { "Use the RunC64Program tool to load and run the final C64 program on the connected Commodore 64 hardware." if hw_access_tools.is_kungfuflash_connected() else "" }
    { "If at any point you need to restart the C64 hardware, use the RestartC64 tool." if testing_tools.is_c64keyboard_connected() else "" }
    { "Use the CaptureC64Screen tool to capture the current screen of the C64 and analyze what is displayed, i.e to verify if the program started and looks good." if testing_tools.is_capture_device_connected() else "" }
    - No need to persist and edit the source code during the creation process, as the agent has external memory to store the current source code.
    - Only save the final source code to a file at the end of the creation process.

    Throughout the process, make use of the todo tool to keep track of your tasks and ensure all steps are completed systematically.
    Communicate with the user in English, even if the game itself is to be created in another language.
"""

program_path = os.path.abspath(f"output")
program_path_relative=program_path[3:] if program_path[1] == ':' else program_path
path_instructions = f"""Always use the path {program_path_relative} to list, load and save files. Don't use drive letters or absolute paths that contain drive letters."""

c64_agent_tools = coding_tools.tools() + testing_tools.tools() + hw_access_tools.tools() + game_design_tools.tools()

deepagent_middleware = [TodoListMiddleware(), FilesystemMiddleware(backend=FilesystemBackend())]

RECURSION_LIMIT = 100

agent = create_agent(
    model=model_agent,
    tools=c64_agent_tools,
    checkpointer=MemorySaver(),
    state_schema=VibeC64AgentState,    
    middleware=deepagent_middleware,
    system_prompt=vibec64_agent_instructions + path_instructions,
).with_config({"recursion_limit": 100})


welcome_message = Markdown(f"""
```
 █████   █████  ███  █████                █████████   ████████  █████ █████ 
░░███   ░░███  ░░░  ░░███                ███░░░░░███ ███░░░░███░░███ ░░███  
 ░███    ░███  ████  ░███████   ██████  ███     ░░░ ░███   ░░░  ░███  ░███ █
 ░███    ░███ ░░███  ░███░░███ ███░░███░███         ░█████████  ░███████████
 ░░███   ███   ░███  ░███ ░███░███████ ░███         ░███░░░░███ ░░░░░░░███░█
  ░░░█████░    ░███  ░███ ░███░███░░░  ░░███     ███░███   ░███       ░███░ 
    ░░███      █████ ████████ ░░██████  ░░█████████ ░░████████        █████ 
     ░░░      ░░░░░ ░░░░░░░░   ░░░░░░    ░░░░░░░░░   ░░░░░░░░        ░░░░░  
                                                                            
```
                           
Welcome to 🎮**VibeC64**, your AI assistant for creating Commodore 64 BASIC games!

I can help you:
- Design and create C64 BASIC games
- Check syntax and fix errors
- Run programs on real hardware (if connected) or in an emulator

""")
console.print(Panel(welcome_message, border_style="blue", padding=(1, 2)))
game_create_task = Prompt.ask("Enter the [bold]game creation task[/bold]")

thread_id = str(uuid.uuid4())

agent_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}

async def run_agent_game_creation():
    async for chunk in agent.astream(  
        {"messages": [{"role": "user", "content": game_create_task}]},
        stream_mode="values",
        config = agent_config,
    ): 
        if "messages" in chunk:
            format_message(chunk["messages"][-1])   
    
if __name__ == "__main__":
    asyncio.run(run_agent_game_creation())
