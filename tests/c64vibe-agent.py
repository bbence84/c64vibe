import os

from deepagents import SubAgent, create_deep_agent
from langchain.chat_models import init_chat_model
from deepagents.backends.filesystem import FilesystemBackend

from dotenv import load_dotenv
load_dotenv(override=True)

from agents.coding_agent import coding_subagent
from utils.formatting import format_messages

model = init_chat_model('gpt-5.1', model_provider="azure_openai") # Uses Azure OpenAI

# Tools for C64Vibe Agent
# - send_text_to_c64
# - create_program
# - syntax_check_program
# - create_test_cases_for_program
# - start_program_on_c64
# - end_program_on_c64
# - restart_c64
# - create_screen_capture_of_c64

# Sub-agents
# - C64 BASIC V2.0 Code Generator (generate code and check syntax)
# - C64 Program Tester (create test cases and run them, check the results)
# - C64 Hardware Controller (send text, take screenshot, start / end program, restart C64)

# System prompt to steer the agent
c64vibe_instructions = """
    You are C64Vibe, an AI Agent specialized in creating software for the Commodore 64 computer.
    Use the various tools and sub-agents at your disposal to create, test, and run C64 BASIC V2.0 programs.
    Follow these guidelines:
    1. When given a user request, first determine if it involves creating or modifying a C64 BASIC V2.0 program.
    2. If code creation or modification is needed, use the C64 BASIC V2.0 Code Generator sub-agent to generate syntactically correct code.

    Once the game source is created, save the game to the output directory and provide the user with the source code.
"""

# Program absolute path
program_path = os.path.abspath("output")

# Create the deep agent
agent = create_deep_agent(
    model=model,
    tools=[],
    #backend=FilesystemBackend(),
    system_prompt=c64vibe_instructions,
    subagents=[coding_subagent],
)

# Invoke the agent
result = agent.invoke({"messages": [{"role": "user", "content": 
    """
    Create a text based adventure game which assumes C64 is still widely used in 2025.
    The game should have at least 20 different locations to explore and 10 different items to collect.
    The player should be able to interact with NPCs and solve puzzles to progress through the story
    """}]})

format_messages(result["messages"]) 