#  █████   █████  ███  █████                █████████   ████████  █████ █████ 
# ░░███   ░░███  ░░░  ░░███                ███░░░░░███ ███░░░░███░░███ ░░███  
#  ░███    ░███  ████  ░███████   ██████  ███     ░░░ ░███   ░░░  ░███  ░███ █
#  ░███    ░███ ░░███  ░███░░███ ███░░███░███         ░█████████  ░███████████
#  ░░███   ███   ░███  ░███ ░███░███████ ░███         ░███░░░░███ ░░░░░░░███░█
#   ░░░█████░    ░███  ░███ ░███░███░░░  ░░███     ███░███   ░███       ░███░ 
#     ░░███      █████ ████████ ░░██████  ░░█████████ ░░████████        █████ 
#      ░░░      ░░░░░ ░░░░░░░░   ░░░░░░    ░░░░░░░░░   ░░░░░░░░        ░░░░░                                                                    
# -----------------------------------------------------------
# VibeC64: Chat UI for AI Assisted C64 Game Creation
# Created by Bence Blaske - 2026
# -----------------------------------------------------------

import os
import uuid
import base64
import logging
import chainlit as cl
from typing import Dict, Optional

from chainlit.input_widget import Select, Switch, TextInput

XCBASIC3_MODE = True

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents.middleware import TodoListMiddleware
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware

from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage

from utils.llm_access import LLMAccessProvider
from utils.chainlit_middleware import ChainlitMiddlewareTracer

from tools.agent_state import VibeC64AgentState
from tools.coding_tools import CodingTools
from tools.testing_tools import TestingTools
from tools.game_design_tools import GameDesignTools
from tools.hw_access_tools import HWAccessTools

from dotenv import load_dotenv
env_file = os.getenv("ENV_FILE", ".env")
load_dotenv(env_file)

RECURSION_LIMIT = 100  # Increase recursion limit for complex tasks if the agent needs to iterate over the task in many steps
USE_FILE_SYSTEM = False # Set to True to enable file system access for the agent, but this is usually not needed.

set_model_settings_alert = '<span style="color:red">⚠️**Set your AI model and API key in the Settings panel (⚙️ icon in the chat input area below) before proceeding.**⚠️</span>'

@cl.on_chat_start
async def on_chat_start():
    llm_access_provider = LLMAccessProvider()
    cl.user_session.set("llm_access_provider", llm_access_provider)
    cl.user_session.set("hw_access_tools", HWAccessTools()) 
    cl.user_session.set("testing_tools", TestingTools(llm_access=llm_access_provider))    
    
    logger.info("Loading AI model from environment variables if available...")
    load_ai_model_from_env()

    await display_welcome_message()

    await init_settings()
    
    if cl.user_session.get("model_init_success") is not True:
        set_model_settings_alert_msg = await cl.Message(content=set_model_settings_alert).send()
        cl.user_session.set("set_model_settings_alert_msg", set_model_settings_alert_msg)
        return
    
    await initialize_agent()
    
async def initialize_agent():

    llm_access_provider = cl.user_session.get("llm_access_provider")
    hw_access_tools = cl.user_session.get("hw_access_tools")
    testing_tools = cl.user_session.get("testing_tools")

    # Initialize tool classes
    coding_tools = CodingTools(llm_access=llm_access_provider, cl=cl, hw_access_tools=hw_access_tools)
    coding_tools.set_xcbasic3_mode(XCBASIC3_MODE)
    cl.user_session.set("coding_tools", coding_tools)
    
    game_design_tools = GameDesignTools(llm_access=llm_access_provider)

    model_agent = llm_access_provider.get_llm_model()

    if testing_tools.is_c64keyboard_connected() and testing_tools.is_capture_device_connected():
        testing_instructions = f"""
        
        After the game is available (has been created and syntax checked) or loaded into the memory, first use the AnalyzeGameMechanics tool to analyze the game mechanics and learn how to control the game.
        
        If the game is not running yet, use the RunC64Program tool to start the game on the connected Commodore 64 hardware using RunC64Program.        

        Then, use the SendTextToC64 tool to send the necessary key presses based on the output of CaptureC64Screen that shows what is currently displayed on the C64 screen.
        Continue to iterate between CaptureC64Screen and SendTextToC64 to play and test the game on the real C64 hardware.
        If you enter a command using SendTextToC64, you usually need to also press Enter afterwards to confirm the command.
        If you only need to send a single keystroke, i.e. "Return", "Space", "0", "1", ..., "9", use the single_key parameter as true of SendTextToC64 to true and send text like "Return" .
        You can send multiple key presses at once using SendTextToC64, i.e to type in GO SOUTH, but only use commands that are relevant to the current game state and game.
        If at any point the game seems stuck or glitchy or an error is shown, stop the testing process and tell the user about the issue.

        """
    else: 
        testing_instructions = ""
        
    if XCBASIC3_MODE:
        language_specific_instructions = f"""
        The programs will be created in XC=BASIC 3 language mode. Ensure that the generated code is fully compatible with XC=BASIC 3 syntax and features.
        """
    else:
        language_specific_instructions = f"""
        The programs will be created in standard Commodore 64 BASIC 2.0 language mode. Ensure that the generated code is fully compatible with standard C64 BASIC syntax and features."""

    
    vibec64_agent_instructions = f"""
    You are VibeC64, an AI Agent specialized in creating games for the Commodore 64 computer.
    Use the various tools at your disposal to create, test, and run C64 games.
    When given a user request, first determine if it involves creating or modifying a C64 program source code.

    Right at the beginning of the game creation or modification process, don't start using the tools right away, but emit a short statement that the process has been started and mention the initial steps you will take. Don't use Chinese though fragments.
    
    {language_specific_instructions}
    
    Tool use instructions:
    - If code creation or modification is needed, first use the DesignGamePlan tool to create a detailed game design plan 
    - Use the CreateUpdateC64ProgramCode tool to generate syntactically correct code based on the design plan created by DesignGamePlan. Don't specify code in the description, only the design plan.
       - The CreateUpdateC64ProgramCode tool should recieve all the details from the game design plan, how the code should be generated, what features to include etc.
    - After generating the code, use the SyntaxChecker tool to ensure there are no syntax errors.
    - If there are syntax errors, correct them using the FixSyntaxErrors tool and re-check them using the SyntaxChecker tool until the code is error-free.
    - No need to persist and edit the source code during the creation process, as the agent has external memory to store the current source code.

    {testing_instructions}        

    At the end of the process, don't provide links to the PRG or BAS files, just state that the files are ready for download or execution.
    Throughout the process, make use of the write_todos tool to keep track of your tasks and ensure all steps are completed systematically.
    Communicate with the user in English, even if the game itself is to be created in another language.
    At the end of the tasks, update the todo list with write_todos to mark all tasks as completed.


    """
    path_instructions = ""
    if USE_FILE_SYSTEM:
        program_path = os.path.abspath(f"output")
        program_path_relative = program_path[3:] if program_path[1] == ':' else program_path
        path_instructions = f"""Always use the path {program_path_relative} to list, load and save files, but only save if needed. Don't use drive letters or absolute paths that contain drive letters."""
        
    # Combine all tools
    c64_agent_tools = coding_tools.tools() + testing_tools.tools() + hw_access_tools.tools() + game_design_tools.tools()

    # Setup middleware with Chainlit tracer
    middleware = [
        TodoListMiddleware(),
        ChainlitMiddlewareTracer()
    ]

    if USE_FILE_SYSTEM:
        middleware.append(FilesystemMiddleware(backend=FilesystemBackend()))
    
    # Create the agent
    agent = create_agent(
        model=model_agent,
        tools=c64_agent_tools,
        middleware=middleware,
        checkpointer=MemorySaver(),
        state_schema=VibeC64AgentState,
        system_prompt=vibec64_agent_instructions + path_instructions,
    ).with_config({"recursion_limit": RECURSION_LIMIT})

    # Store agent in session
    cl.user_session.set("agent", agent)
    cl.user_session.set("thread_id", str(uuid.uuid4()))


async def display_welcome_message():
    """
    Displays the welcome message with hardware status information.
    """
    hw_access_tools = cl.user_session.get("hw_access_tools")
    testing_tools = cl.user_session.get("testing_tools")

    hardware_status = []
    if hw_access_tools.is_c64u_api_connected():
        hardware_status.append("- ✓ Commodore 64 Ultimate connected - ready to run programs directly on real C64 hardware")
    if hw_access_tools.is_kungfuflash_connected():
        hardware_status.append("- ✓ KungFu Flash connected - ready to run programs directly on real C64 hardware")

    if testing_tools.is_c64keyboard_connected():
        hardware_status.append("- ✓ C64 Keyboard connected - can send keypresses to real C64 hardware")
    if testing_tools.is_capture_device_connected():
        hardware_status.append("- ✓ Capture device connected - can capture screen from real C64 hardware")
    
    hardware_info = "\n".join(hardware_status) if hardware_status else "- No Commodore 64 hardware connected - you can still create and test programs in an emulator or download the programs and run them manually on real hardware."
    register_llm_provider_text = ""
    register_llm_provider_text = f"""
### Getting an AI Model Provider API Key
In order to use this app, you need to register an AI model provider account through either OpenRouter or directly with the vendor. OpenRouter allows you to use multiple AI models from different providers with a single API key. 
[Get an API key](https://openrouter.ai/settings/keys) after registration and [adding credits](https://openrouter.ai/settings/credits). You can also get API keys directly, i.e. in [Google AI Studio](https://aistudio.google.com/app/api-keys). There's free quota, but it's pretty limited, so you also need to enable billing. For best experience and cost efficiency, we recommend using the **Google Gemini 3.0 Flash Preview model**.
"""
    
    welcome_message = f"""## VibeC64 (BETA) - AI-Powered Commodore 64 Game Creator 

Welcome to **VibeC64**, your AI assistant for creating Commodore 64 games!

I can help you:
- Design and create C64 games
- Check syntax and fix errors (even after creating the game)
- Run programs on real hardware (if connected) or in an emulator
### Hardware Status
{hardware_info}

{register_llm_provider_text}
"""
    welcome_msg = await cl.Message(content=welcome_message).send()
    cl.user_session.set("welcome_msg", welcome_msg)
    

def load_ai_model_from_env():
    model_provider = os.getenv("AI_MODEL_PROVIDER")
    model_name = os.getenv("AI_MODEL_NAME")     
    api_key = os.getenv("API_KEY")

    if model_provider and model_name:
        use_openrouter = False
        if model_provider == "openrouter":
            use_openrouter = True
        
        llm_access_provider = cl.user_session.get("llm_access_provider")
        try:
            llm_access_provider.set_llm_model(model_name_technical=model_name, model_provider=model_provider, api_key=api_key, use_openrouter=use_openrouter)
        except Exception as e:
            logger.error(f"Error setting LLM model from env: {e}")
            cl.user_session.set("model_init_success", False)
            return
        cl.user_session.set("llm_access_provider", llm_access_provider)
        cl.user_session.set("model_init_success", True)
    else:
        cl.user_session.set("model_init_success", False)


async def init_settings():
    settings = await cl.ChatSettings(
        [
            Select(
                id="LLMSelector",
                label="LLM Model",
                values=["Google Gemini 3.0 Flash Preview", "Google Gemini 3.0 Pro"], #,"Anthropic Claude 4.5 Sonnet", "Anthropic Claude 4.5 Opus", "OpenAI GPT-5", "OpenAI GPT-5.2"],
                initial_index=0,
            ),
            Switch(id="OpenRouter", label="Model access via OpenRouter", initial=False),
            TextInput(
                id="APIKey",
                label="API Key",
                placeholder="Enter your API key here"),
            Switch(id="XCBasic3", label="XC=BASIC 3 Mode (Experimental)", initial=XCBASIC3_MODE),
        ]).send()
    return settings

@cl.on_window_message
async def on_window_message(message: dict):
    if "command" in message:
        command = message["command"]
        hw_access_tools = cl.user_session.get("hw_access_tools")
        current_source_code = message.get("basic_source_code", "")
        if command == "start_program_on_c64u":
            response = hw_access_tools.run_c64_program_c64u_api(current_source_code)
        elif command == "start_program_on_kungfu":
            response = hw_access_tools.run_c64_program_kungfu(current_source_code)
        logger.info(f"Hardware command for program RUN response: {response}")

@cl.on_settings_update
async def on_settings_update(settings):
    cl.user_session.set("settings", settings)
    await change_agent_settings(settings)

@cl.on_message
async def on_message(message: cl.Message):

    welcome_msg = cl.user_session.get("welcome_msg")
    if welcome_msg is not None:
        await welcome_msg.remove()
    set_model_settings_alert_msg = cl.user_session.get("set_model_settings_alert_msg") 

    if cl.user_session.get("model_init_success") is not True:
        if set_model_settings_alert_msg is not None:
            await set_model_settings_alert_msg.remove() 
        set_model_settings_alert_msg = await cl.Message(content=set_model_settings_alert).send()
        cl.user_session.set("set_model_settings_alert_msg", set_model_settings_alert_msg)
        return

    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id") 
    

    agent_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}

    additional_messages = get_messages_from_attachments(message)

    if additional_messages != []:
        logger.info(f"Additional messages from attachments found: {len(additional_messages)}")
        agent_messages = [{"role": "user", "content": [{"type": "text", "text": message.content}, *additional_messages]}] 
    else:
        agent_messages = [{"role": "user", "content": message.content}]           

    msg = cl.Message(content="")
    await msg.send()

    async for stream_mode, data  in agent.astream(
         config=agent_config,
         stream_mode=["messages"],  # stream_mode=["messages", "updates"],  
         input={"messages": agent_messages},
    ):
        if stream_mode == "messages":
            token, metadata = data
            if isinstance(token, AIMessageChunk):
                await msg.stream_token(token.text)

    await msg.update()

    task_list = cl.user_session.get("task_list")
    if task_list is not None:
        task_list.status = "Done"
        await task_list.send()
        cl.user_session.set("task_list_completed", True)

def get_messages_from_attachments(message: cl.Message):
    additional_messages = []
    if message.elements:
        attachments = [file for file in message.elements if
                                "text/plain" in file.mime or 
                                "image/png" in file.mime or 
                                "image/jpg" in file.mime or
                                "image/jpeg" in file.mime or
                                "application/octet-stream" in file.mime]       
        for uploaded_file in attachments:
            if uploaded_file.mime.startswith("image/"):
                file_type = "image"
            else:
                file_type = "text"

            if file_type == "image":
                with open(uploaded_file.path, "rb") as image_file:
                    file_buffer = image_file.read()
                    b64 = base64.b64encode(file_buffer).decode()
                    img_message = { "type": "image_url", "image_url": { "url": f"data:image/png;base64,{b64}" , },}                
                    additional_messages.append(img_message)
            else:
                try:
                    with open(uploaded_file.path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                        file_is_binary = False
                except Exception as e:
                    file_is_binary = True
                if not file_is_binary:
                    additional_messages.append({ "type": "text", "text": file_content })
    return additional_messages

async def change_agent_settings(settings):
    llm_model = settings["LLMSelector"]
    api_key = settings["APIKey"]
    use_openrouter = settings["OpenRouter"]
    XCBASIC3_MODE = settings["XCBasic3"]


    llm_access_provider = cl.user_session.get("llm_access_provider")

    coding_tools = cl.user_session.get("coding_tools")
    if coding_tools:
        coding_tools.set_xcbasic3_mode(XCBASIC3_MODE)

    if llm_access_provider and llm_model != "" and api_key != "" and llm_model is not None and api_key is not None:
        logging.info(f"Changing AI model to {llm_model} using OpenRouter: {use_openrouter}")
        set_llm_success = llm_access_provider.set_llm_model(model_name=llm_model, api_key=api_key, use_openrouter=use_openrouter)
        if not set_llm_success:

            cl.user_session.set("model_init_success", False)
            model_init_failure_alert = set_model_settings_alert + '<br>❌<span style="color:red"> **Error initializing the selected model. Please check your API key and model selection.**</span>'
            set_model_settings_alert_msg = cl.user_session.get("set_model_settings_alert_msg") 
            if set_model_settings_alert_msg is None:
                set_model_settings_alert_msg = await cl.Message(content=model_init_failure_alert).send()
                cl.user_session.set("set_model_settings_alert_msg", set_model_settings_alert_msg)
            else:
                set_model_settings_alert_msg.content = model_init_failure_alert
                await set_model_settings_alert_msg.update()
                cl.user_session.set("set_model_settings_alert_msg", set_model_settings_alert_msg)

            return
        
        cl.user_session.set("llm_access_provider", llm_access_provider)
        cl.user_session.set("model_init_success", True)
        await initialize_agent()
            
        set_model_settings_alert_msg = cl.user_session.get("set_model_settings_alert_msg") 
        if set_model_settings_alert_msg is not None:
            await set_model_settings_alert_msg.remove()
            set_model_settings_alert_msg = None    

# Run Chainlit if this script is executed directly
if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)