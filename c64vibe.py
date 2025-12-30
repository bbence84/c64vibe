#  ██████╗ ██████╗ ██╗  ██╗    ██╗   ██╗██╗██████╗ ███████╗
# ██╔════╝██╔════╝ ██║  ██║    ██║   ██║██║██╔══██╗██╔════╝
# ██║     ███████╗ ███████║    ██║   ██║██║██████╔╝█████╗  
# ██║     ██╔═══██╗╚════██║    ╚██╗ ██╔╝██║██╔══██╗██╔══╝  
# ╚██████╗╚██████╔╝     ██║     ╚████╔╝ ██║██████╔╝███████╗
#  ╚═════╝ ╚═════╝      ╚═╝      ╚═══╝  ╚═╝╚═════╝ ╚══════╝
# -----------------------------------------------------------
# C64Vibe: An AI Agent for Commodore 64 Program Creation
# Created by Bence Blaske - 2025
# -----------------------------------------------------------                                       

# TODO
# -----------------------------
# - Convert to web based UI, with prg conversion and later syntax fixer feature and the way to specify API keys
# ✓ Implement C64 "hardware" functions (loading/running/stopping programs, sending text to screen, restarting)
# ✓ Use LangChain states for passing source code and large tool inputs / outputs in the context
# - Human in the loop for approval before creating the source code and starting the program on C64
# ✓ Find C64 game source codes for few shot learning
# ✓ Use Kungfu Flash or similar for program loading/running/restart?
# ✓ Camera input for screen capture
# ✓ Create library for remote C64 keyboard input
# ✓ LLM streaming response handling
# - Test case generation and execution
# - Investigate graphics creation externally, maybe based on generative AI models and then convert to C64 format
# ✓ Deep agent: use the todo middleware for better step-by-step execution control
# - Check if VINE or similar C64 emulators have APIs / command line tools for i.e syntax checking
# - Make a CLI version of the agent for local use
# ✓ Add LLM based syntax checking tool
# - Ability to specify LLM provider and model in .env
# ✓ Check if C64 is connected, if not, fall back without hardware access  
# - Check if thinking mode is better vs. non thinking mode for Gemini
# - Improve error handling and logging
# - Fix file save https://github.com/langchain-ai/deepagents/pull/336

# Tools for C64Vibe Agent
# - create_program          DONE   
# - syntax_check_program    DONE    
# - fix_syntax_errors       DONE
# - design_game_plan        DONE
# - logic_code_review       
# - create_test_cases
# - run_c64_program         DONE
# - restart_c64             DONE
# - capture_c64_screen      DONE

import os
import uuid
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent

from langchain.agents.middleware import HumanInTheLoopMiddleware, InterruptOnConfig, TodoListMiddleware
from deepagents.middleware.filesystem import FilesystemMiddleware

from utils.formatting import format_messages, format_message
import utils.llm_access as llm_access

from tools.agent_state import C64VibeAgentState
from tools.coding_tools import CodingTools
from tools.testing_tools import TestingTools
from tools.hw_access_tools import HWAccessTools

model_coder = llm_access.get_gemini_model('gemini-3-flash-preview')
model_agent = llm_access.get_gemini_model('gemini-3-flash-preview')
model_screen_ocr = llm_access.get_gemini_model('gemini-3-flash-preview')
# model_agent = llm_access.get_openai_model('gpt-4.1', azure_openai=True)

coding_tools = CodingTools(model_coder=model_coder)
testing_tools = TestingTools(model_coder=model_coder, model_screen_ocr=model_screen_ocr)
hw_access_tools = HWAccessTools()

c64vibe_agent_instructions = f"""
    You are C64Vibe, an AI Agent specialized in creating games for the Commodore 64 computer.
    Use the various tools and at your disposal to create, test, and run C64 BASIC V2.0 games.
    When given a user request, first determine if it involves creating or modifying a C64 BASIC V2.0 game.

    Tool use instructions:
    - If code creation or modification is needed, first use the DesignGamePlan tool to create a detailed game design plan 
    - Use the WriteC64BasicCode tool to generate syntactically correct code based on the design plan created by DesignGamePlan. Don't specify code in the description, only the design plan.
    - After generating the code, use the SyntaxChecker tool to ensure there are no syntax errors.
    - If there are syntax errors, correct them using the FixSyntaxErrors tool and re-check them using the SyntaxChecker tool until the code is error-free.
    { "Use the RunC64Program tool to load and run the final C64 BASIC V2.0 program on the connected Commodore 64 hardware." if hw_access_tools.is_kungfuflash_connected() else "" }
    { "If at any point you need to restart the C64 hardware, use the RestartC64 tool." if hw_access_tools.is_c64keyboard_connected() else "" }
    { "Use the CaptureC64Screen tool to capture the current screen of the C64 and analyze what is displayed, i.e to verify if the program started and looks good." if testing_tools.is_capture_device_connected() else "" }
    - No need to persist and edit the source code during the creation process, as the agent has external memory to store the current source code.
    - Only save the final source code to a file at the end of the creation process.

    Throughout the process, make use of the todo tool to keep track of your tasks and ensure all steps are completed systematically.
    Communicate with the user in English, even if the game itself is to be created in another language.
"""

program_path = os.path.abspath(f"output")
program_path_relative=program_path[3:] if program_path[1] == ':' else program_path
path_instructions = f"""Always use the path {program_path_relative} to list, load and save files. Don't use drive letters or absolute paths that contain drive letters."""

c64_agent_tools = coding_tools.tools() + testing_tools.tools() + hw_access_tools.tools()

deepagent_middleware = [TodoListMiddleware(), FilesystemMiddleware(backend=FilesystemBackend())]

agent = create_agent(
    model=model_agent,
    tools=c64_agent_tools,
    checkpointer=MemorySaver(),
    state_schema=C64VibeAgentState,    
    middleware=deepagent_middleware,
    system_prompt=c64vibe_agent_instructions + path_instructions,
)
game_create_task = f"""A text based game in Hungarian about the political situation, and corruption in Hungary today, 
about Orban and his oligarchs. The plot is to win on the next elections held in 2026, by all non-legal means.
The game should be satirical and humorous. Game should be in Hungarian.
The game should have at least 20 different locations and situations to explore.
Include simple graphics using PETSCII characters and sound effects where appropriate."""

agent_config = {"configurable": {"thread_id": str(uuid.uuid4())}}

for chunk in agent.stream(  
    {"messages": [{"role": "user", "content": game_create_task}]},
    stream_mode="values",
    config = agent_config,
): 
    if "messages" in chunk:
        format_message(chunk["messages"][-1])    