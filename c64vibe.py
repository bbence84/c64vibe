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
# - Use LangChain states for passing source code and large tool inputs / outputs in the context
# - Human in the loop for approval before creating the source code and starting the program on C64
# ✓ Find C64 game source codes for few shot learning
# ✓ Use Kungfu Flash or similar for program loading/running/restart?
# - Optional: Split up the agent to subagents: design agent, coding agent, tester agent, C64 hw interface agent
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
# - end_program_on_c64
# - restart_c64             DONE
# - capture_c64_screen      DONE

import os
import base64
import time
import uuid
from deepagents import SubAgent, create_deep_agent
from langchain.chat_models import init_chat_model
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from utils.formatting import format_messages, format_message
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from typing import Annotated
import utils.c64_syntax_checker as c64_syntax_checker
import utils.llm_access as llm_access
import utils.c64_hw as c64_hw
from utils.kungfuflash_usb import KungFuFlashUSB
import utils.agent_utils as agent_utils

from rich.prompt import Prompt

from dotenv import load_dotenv
load_dotenv(override=True)

#model_agent = llm_access.get_openai_model('gpt-4.1', azure_openai=True)
#model_coder = llm_access.get_openai_model('gpt-4.1', azure_openai=True)
model_agent = llm_access.get_gemini_model('gemini-3-pro-preview')
model_coder = llm_access.get_gemini_model('gemini-3-pro-preview')
model_screen_ocr = llm_access.get_gemini_model('gemini-3-pro-preview')
#model_screen_ocr = llm_access.get_openai_model('gpt-4.1', azure_openai=True)

# TODO: Check if capture device is connected (i.e. webcam or USB video capture device)
capture_device_connected = False

try:
    kungfu_flash_port = os.getenv("KUNGFU_FLASH_PORT", "COM4")
    kungfuflash = KungFuFlashUSB(port=kungfu_flash_port)
    kungfuflash_connected = True
except Exception as e:
    print(f"Warning: Could not connect to KungFuFlash on port {kungfu_flash_port}. Continuing without KungFuFlash access.")
    kungfuflash_connected = False

try:
    keyboard_port = os.getenv("C64_KEYBOARD_DEVICE_PORT", "COM3")
    c64keyboard = c64_hw.C64HardwareAccess(device_port=keyboard_port, baud_rate=19200, debug=False)
    c64keyboard_connected = True
except Exception as e:
    print(f"Warning: Could not connect to C64 keyboard hardware on port {keyboard_port}. Continuing without keyboard access.")
    c64keyboard_connected = False

@tool("CaptureC64Screen", description="Captures the current screen of the C64 and returns what is displayed")
def capture_c64_screen(program_specifications: Annotated[str, "What the program should do in theory."] = "") -> str:

    # Capture the screen from the C64 hardware using the webcam
    image_path = agent_utils.get_webcam_snapshot()

    # Encode the image to base64 for sending to the LLM
    b64 = agent_utils.encode_image(image_path)
    img_base64 = f"data:image/png;base64,{b64}"
    img_message = { "type": "image_url", "image_url": { "url": img_base64, },}

    # OCR the image using a multimodal LLM
    ocr_results = model_screen_ocr.invoke([
        {"role": "system", "content": "You know understand Commodore 64 screens, how program listings and outputs look like. You know how C64 programs and games look like. You can read text from images of C64 screens accurately."},
        {"role": "user",  "content": 
         [ {"type": "text", "text": 
            f"""
            Please analyze the image carefully and return what you see. If it's a simple text based program, return it as pure text, properly idented and formatted. If it's a graphical screen i.e. a game, describe what you can see and tell if there's anything unusual i.e. error messages and exception, etc."""
            if program_specifications == "" else
            f"""
            The program was supposed to do the following: {program_specifications}. Please also compare what you see on the screen with what the program was supposed to do.
            """
              }, img_message,]},
    ])
    return ocr_results.content

@tool("DesignGamePlan", description="Creates a detailed game design plan for a Commodore 64 game based on a description")
def create_game_design_plan(description: str) -> str:
    design_instructions = f""" Create a detailed game design plan for a game for the Commodore 64 computer based on the following description:
        {description}
        The design plan should include:
        - Game setting and storyline
        - Main characters and NPCs
        - Locations to explore
        - Items to collect
        - Puzzles and challenges to solve
        - Interaction mechanics with NPCs and environment
        Provide the design plan in a structured format, using Markdown.
        """
    llm_design_response = model_coder.invoke([{"role": "user", "content": design_instructions}])
    return llm_design_response.content

@tool("SyntaxChecker", description="Checks the syntax of C64 BASIC V2.0 source code")
def check_syntax(source_code: Annotated[str, "The source code to check"], 
                 llm_based: Annotated[bool, "The syntax check is performed by an LLM"] = True) -> str:
    if llm_based:
        syntax_check_instructions = f""" Check the following C64 BASIC V2.0 source code for syntax errors:
            {source_code}
            List any syntax errors found, or state that there are no syntax errors.
            Provide only the list of syntax errors or confirmation of no errors as output.
            Syntax errors should be described clearly with line numbers where applicable.
            """
        llm_checker_response = model_coder.invoke([{"role": "user", "content": syntax_check_instructions}])
        return llm_checker_response.content
    else:
        return c64_syntax_checker.check_source(source_code, return_structured=False, print_errors=False, return_warnings=False)    

@tool("WriteC64Code", description="Generates C64 BASIC V2.0 source code based on a description")
def create_source_code(
    description: Annotated[str, "Description of the program to create, including the game design plan if applicable"],
    ) -> str:
    code_create_instructions = f""" Generate a syntactically correct C64 BASIC V2.0 program based on the following description:
        {description}
        Ensure the code adheres to C64 BASIC V2.0 syntax and conventions.
        Make sure line numbers are included and correctly ordered, and there's no duplicate line numbers.
        Provide only the source code as output, nothing else.
        C64 BASIC V2.0 has the following rules:
        - Maximum 80 characters per line
        - Line numbers must be between 1 and 63999
        - Line numbers must be in increments of 10
        - Only use commands and functions available in C64 BASIC V2.0
        - No lowercase letters, only uppercase
        - No special characters outside of those supported by C64 BASIC V2.0, only use PETSCII characters.
        - Don't use accented characters, even for non-English programs.

        Example BASIC V2.0 programs for reference, to follow C64 BASIC V2.0 syntax:
        {agent_utils.read_example_programs(num_examples=5)}

        Again, the task is to generate a syntactically correct C64 BASIC V2.0 program based on the description provided:
        {description}

        Consider all the details in the description when generating the code, i.e. graphics, sound effects, gameplay mechanics, etc.
        Make sure the code is ready to run on a real Commodore 64 computer without syntax errors.

        Communicate only in English, even if the program itself is to be created in another language.
        """
    llm_coder_response = model_coder.invoke([{"role": "user", "content": code_create_instructions}])
    return llm_coder_response.content

@tool("FixSyntaxErrors", description="Fixes syntax errors in C64 BASIC V2.0 source code")
def fix_syntax_errors(
        source_code: Annotated[str, "C64 BASIC V2.0 source code with potential syntax errors"],
        syntax_errors: Annotated[str, "Description of the syntax errors identified in the source code"]) -> str:
    fix_instructions = f""" The following C64 BASIC V2.0 source code contains syntax errors:
        {source_code}
        Syntax errors identified:
        {syntax_errors}
        Provide only the corrected source code as output.
        """
    llm_coder_response = model_coder.invoke([{"role": "user", "content": fix_instructions}])
    return llm_coder_response.content

# @tool("RunC64Program", description="Loads and runs a C64 BASIC V2.0 program on the connected Commodore 64 hardware")
# def run_c64_program(source_code: str) -> str:
#     c64hw.run_program_from_text(source_code, restart_c64=True)
#     return "Program loaded and started on the Commodore 64 hardware."

@tool("RunC64Program", description="Loads and runs a C64 BASIC V2.0 program on the connected Commodore 64 hardware")
def run_c64_program(source_code: str) -> str:

    # Write / overwrite the source code to a temporary PRG file
    temp_bas_path = os.path.join("output", "temp_program.bas")
    with open(temp_bas_path, "w") as temp_bas_file:
        temp_bas_file.write(source_code)
    
    # Convert the source code to a PRG file
    temp_prg_path = agent_utils.convert_c64_bas_to_prg(temp_bas_path)

    with kungfuflash as kff:
        kff.return_to_menu(reconnect=True)
        time.sleep(1)  # Wait for menu to load
        # print(f"Connected to KungFuFlash on {kff.get_port()}")
        # print(f"Sending {temp_prg_path} program via USB...")
        success = kff.send_prg(temp_prg_path)
        if success:
            return "Program loaded and started on the Commodore 64 hardware."
        else:
            return "Failed to send program to Commodore 64 hardware."
    

@tool("RestartC64", description="Restarts the connected Commodore 64 hardware")
def restart_c64():
    c64keyboard.restart_c64()
    return "Commodore 64 restarted."

# System prompt to steer the agent
c64vibe_instructions = f"""
    You are C64Vibe, an AI Agent specialized in creating games for the Commodore 64 computer.
    Use the various tools and at your disposal to create, test, and run C64 BASIC V2.0 games.
    When given a user request, first determine if it involves creating or modifying a C64 BASIC V2.0 game.

    Tool use instructions:
    - If code creation or modification is needed, first use the DesignGamePlan tool to create a detailed game design plan 
    - Use the WriteC64Code tool to generate syntactically correct code based on the design plan created by DesignGamePlan.
    - After generating the code, use the SyntaxChecker tool to ensure there are no syntax errors.
    - If there are syntax errors, correct them using the FixSyntaxErrors tool and re-check them using the SyntaxChecker tool until the code is error-free.
    { "Use the RunC64Program tool to load and run the final C64 BASIC V2.0 program on the connected Commodore 64 hardware." if kungfuflash_connected else "" }
    { "If at any point you need to restart the C64 hardware, use the RestartC64 tool." if c64keyboard_connected else "" }
    { "Use the CaptureC64Screen tool to capture the current screen of the C64 and analyze what is displayed, i.e to verify if the program started and looks good." if capture_device_connected else "" }
    - Save the final source code to a file for later processing.

    Throughout the process, make use of the todo tool to keep track of your tasks and ensure all steps are completed systematically.
    Communicate with the user in English, even if the game itself is to be created in another language.
"""

# Program absolute path based on the current folder where the script is run
program_path = os.path.abspath(f"output")
if not os.path.exists(program_path):
    os.makedirs(program_path)
# Remove the drive letter for relative pathing
program_path_relative=program_path[3:] if program_path[1] == ':' else program_path
# Temporary hack because the FilesystemBackend seems to have issues with absolute paths on Windows
path_instructions = f"""Always use the path {program_path_relative} to list, load and save files."""

c64_agent_tools = [
    check_syntax,
    create_source_code,
    fix_syntax_errors,
    create_game_design_plan ]

if c64keyboard_connected:
    c64_agent_tools.extend([restart_c64])

if kungfuflash_connected:
    c64_agent_tools.extend([run_c64_program])

if capture_device_connected:
    c64_agent_tools.extend([capture_c64_screen])

# Create the deep agent
agent = create_deep_agent(
    model=model_agent,
    tools=c64_agent_tools,
    # interrupt_on={
    #     "run_c64_program": {"allowed_decisions": ["approve_and_run", "revise_code"]},  
    # },    
    backend=FilesystemBackend(),
    system_prompt=c64vibe_instructions + path_instructions,
    # checkpointer=checkpointer
)

# game_create_task = """
#     Create a text based adventure about a rabbit exploring a magical forest.
#     The game should have at least 20 different locations to explore and 10 different items to collect.
#     The player should be able to interact with NPCs and solve puzzles to progress through the story.
#     The language of the game should be Hungarian.
#     Include simple graphics using PETSCII characters and sound effects where appropriate.
#     """

game_create_task = f"""A text based game in Hungarian about the political situation, and corruption in Hungary today, 
                        about Orban and his oligarchs. The plot is to win on the next elections held in 2026, by all non-legal means.
                        The game should be satirical and humorous. Game should be in Hungarian."""

def get_user_decision(interrupts, action):
    review_configs = interrupts["review_configs"]        
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}   
    review_config = config_map[action["name"]]
    choices_str = "\n".join([f"{i+1}. {decision}" for i, decision in enumerate(review_config['allowed_decisions'])])
    user_choice = Prompt.ask("Enter your decision:  " + choices_str + "\n Pick one:", choices=[str(i+1) for i in range(len(review_config['allowed_decisions']))], show_choices=True)
    # Map back to decision value
    user_choice = review_config['allowed_decisions'][int(user_choice)-1]
    return user_choice


run_live_agent = True
if run_live_agent == True:
    for chunk in agent.stream(  
        {"messages": [{"role": "user", "content": game_create_task}]},
        stream_mode="values",
    ): 
        if "messages" in chunk:
            format_message(chunk["messages"][-1])    
else:


    model_agent = llm_access.get_gemini_model('gemini-3-pro-preview')
    model_coder = llm_access.get_gemini_model('gemini-3-pro-preview')
    model_agent = llm_access.get_openai_model('gpt-4.1', azure_openai=True)

    @tool("DesingProgramPlanDummy", description="Creates a detailed program plan for a Commodore 64 program based on a description")
    def create_program_design_plan_dummy(description: str) -> str:
        return "A simple hello world program."
    
    @tool("WriteC64CodeDummy", description="Generates C64 BASIC V2.0 source code based on a description")
    def create_source_code_dummy(description: str) -> str:
        return """10 PRINT "HELLO, WORLD!"
        20 GOTO 10
        """
    
    @tool("SyntaxCheckerDummy", description="Checks the syntax of C64 BASIC V2.0 source code")
    def check_syntax_dummy(source_code: str) -> str:
        return "No syntax errors found."
    
    @tool("RestartC64Dummy", description="Restarts the connected Commodore 64 hardware")
    def restart_c64_dummy():
        return "C64 restarted."
    
    @tool("RunC64ProgramDummy", description="Loads and runs a C64 BASIC V2.0 program on the connected Commodore 64 hardware")
    def run_c64_program_dummy(source_code: str) -> str:
        return "Program started on C64."
    
    #@tool("RunTestPrgOnC64", description="Sends a test PRG file to the C64 via KungFuFlash and runs it")
    def run_test_prg_on_c64():
        test_prg_path = os.path.join("output", "temp_program.prg")
        with kungfuflash as kff:
            print(f"Connected to KungFuFlash on {kungfu_flash_port}")
            print(f"Sending {test_prg_path} program via USB...")
            #kff.return_to_menu()
            #time.sleep(8)  # Wait for menu to load
            success = kff.send_prg(test_prg_path, verbose=False)
            if success:
                print("Program sent and started successfully!")
            else:
                print("Failed to send program.")

    
    # time.sleep(3)  # Wait for menu to load  
    # run_test_prg_on_c64()
    # kungfuflash.connect()
    # time.sleep(3)
    # kungfuflash.return_to_menu()
    



    # test_agent = create_deep_agent(
    #     model=model_agent,
    #     tools=[
    #         run_test_prg_on_c64,
    #         # create_program_design_plan_dummy,
    #         # create_source_code_dummy,
    #         # check_syntax_dummy,
    #         # restart_c64_dummy,
    #         # run_c64_program_dummy,
    #     ],
    #     checkpointer=MemorySaver(),
    #     # interrupt_on={
    #     #     "DesingProgramPlanDummy": {"allowed_decisions": ["approve", "edit", "reject"]},  
    #     #     "WriteC64CodeDummy": {"allowed_decisions": ["approve", "edit", "reject"]},
    #     #     "RestartC64Dummy": {"allowed_decisions": ["approve", "reject"]},
    #     # },          
    #     backend=FilesystemBackend(),
    #     system_prompt=f"""Run test program on the connected C64 via KungFuFlash.""",
    #     #system_prompt=f"You can create a program design plan. Then you can create source code. Check syntax of the created code. Restart the C64 then run the program created. Use the tools as instructed. ALWAYS USE THE FOLDER {program_path_relative} TO LIST, LOAD AND SAVE FILES. Don't specify the drive letter."
    # )

    # agent_config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # program_create_task = """
    #     Create a C64 BASIC V2.0 program that displays "HELLO, WORLD!" on the screen in a loop.
    #     """
    
    # program_create_task = """Run the test program on the connected C64 via KungFuFlash."""

    # # Initial user request
    # current_input = {"messages": [{"role": "user", "content": program_create_task}]}
    
    # while True:
    #     interrupted = False
    #     last_chunk = None
        
    #     # Stream the agent execution
    #     for chunk in test_agent.stream(  
    #         current_input,
    #         stream_mode="values",
    #         config = agent_config,
    #     ): 
    #         last_chunk = chunk
    #         if "messages" in chunk:
    #             format_message(chunk["messages"][-1])  

    #         if "__interrupt__" in chunk:
    #             interrupted = True
    #             interrupts = chunk["__interrupt__"][0].value
    #             action_requests = interrupts["action_requests"]
    #             review_configs = interrupts["review_configs"]        

    #             # Create a lookup map from tool name to review config
    #             config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    #             decisions = []
    #             # Display the pending actions to the user
    #             for action in action_requests:
    #                 decision = get_user_decision(interrupts, action) 
    #                 decisions.append({"type": decision})        
        
    #             # Resume with the user's decisions
    #             current_input = Command(resume={"decisions": decisions})
        
    #     # If there were interrupts, continue the loop to process the resumed execution
    #     if interrupted:
    #         continue
            
    #     # Check if the agent has actually finished (no more steps to execute)
    #     # If last_chunk exists and has no pending actions, we're done
    #     if last_chunk is not None:
    #         # The stream completed without interruption, agent is done
    #         break
    #     else:
    #         # This shouldn't happen, but if it does, exit to avoid infinite loop
    #         break  
