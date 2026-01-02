#  ██████╗ ██████╗ ██╗  ██╗    ██╗   ██╗██╗██████╗ ███████╗
# ██╔════╝██╔════╝ ██║  ██║    ██║   ██║██║██╔══██╗██╔════╝
# ██║     ███████╗ ███████║    ██║   ██║██║██████╔╝█████╗  
# ██║     ██╔═══██╗╚════██║    ╚██╗ ██╔╝██║██╔══██╗██╔══╝  
# ╚██████╗╚██████╔╝     ██║     ╚████╔╝ ██║██████╔╝███████╗
#  ╚═════╝ ╚═════╝      ╚═╝      ╚═══╝  ╚═╝╚═════╝ ╚══════╝
# -----------------------------------------------------------
# C64Vibe UI: Chainlit Web Interface for C64 Program Creation
# Created by Bence Blaske - 2026
# -----------------------------------------------------------

import os
import uuid
import chainlit as cl
from typing import Dict, Optional

from chainlit.input_widget import Select, Switch, TextInput

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents.middleware import TodoListMiddleware
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware

from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage

from utils.llm_access import LLMAccessProvider
from utils.chainlit_middleware import ChainlitMiddlewareTracer
import utils.agent_utils as agent_utils

from tools.agent_state import C64VibeAgentState
from tools.coding_tools import CodingTools
from tools.testing_tools import TestingTools
from tools.game_design_tools import GameDesignTools
from tools.hw_access_tools import HWAccessTools

from dotenv import load_dotenv
load_dotenv()

set_model_settings_alert = '<span style="color:red">⚠️**Set your AI model and API key in the Settings panel (⚙️ icon in the chat input area below) before proceeding.**⚠️</span>'

# @cl.oauth_callback
# def oauth_callback(
#   provider_id: str,
#   token: str,
#   raw_user_data: Dict[str, str],
#   default_user: cl.User,
# ) -> Optional[cl.User]:
#   return default_user

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("llm_access_provider", LLMAccessProvider())
    cl.user_session.set("hw_access_tools", HWAccessTools())

    load_ai_model_from_env()

    await init_settings()
    await display_welcome_message()

    global set_model_settings_alert_msg

    if cl.user_session.get("model_init_success") is not True:
        set_model_settings_alert_msg = await cl.Message(content=set_model_settings_alert).send()
        return
    
    await initialize_agent()
    
async def initialize_agent():

    llm_access_provider = cl.user_session.get("llm_access_provider")
    hw_access_tools = cl.user_session.get("hw_access_tools")

    # Initialize tool classes
    coding_tools = CodingTools(llm_access=llm_access_provider, cl=cl)
    testing_tools = TestingTools(llm_access=llm_access_provider, capture_device_connected=hw_access_tools.is_capture_device_connected())
    game_design_tools = GameDesignTools(llm_access=llm_access_provider)

    model_agent = llm_access_provider.get_llm_model()

    c64vibe_agent_instructions = f"""
    You are C64Vibe, an AI Agent specialized in creating games for the Commodore 64 computer.
    Use the various tools at your disposal to create, test, and run C64 BASIC V2.0 games.
    When given a user request, first determine if it involves creating or modifying a C64 BASIC V2.0 game.

    Tool use instructions:
    - Before starting the creation or modification process, state that the process has been started and mention the initial steps you will take.
    - If code creation or modification is needed, first use the DesignGamePlan tool to create a detailed game design plan 
    - Use the CreateUpdateC64BasicCode tool to generate syntactically correct code based on the design plan created by DesignGamePlan. Don't specify code in the description, only the design plan.
       - The CreateUpdateC64BasicCode tool should recieve all the details from the game design plan, how the code should be generated, what features to include etc.
    - After generating the code, use the SyntaxChecker tool to ensure there are no syntax errors.
    - If there are syntax errors, correct them using the FixSyntaxErrors tool and re-check them using the SyntaxChecker tool until the code is error-free.
    {"- Use the RunC64Program tool to load and run the final C64 BASIC V2.0 program on the connected Commodore 64 hardware." if hw_access_tools.is_kungfuflash_connected() else ""}
    {"- If at any point you need to restart the C64 hardware, use the RestartC64 tool." if hw_access_tools.is_c64keyboard_connected() else ""}
    {"- Use the CaptureC64Screen tool to capture the current screen of the C64 and analyze what is displayed, i.e to verify if the program started and looks good." if hw_access_tools.is_capture_device_connected() else ""}
    - No need to persist and edit the source code during the creation process, as the agent has external memory to store the current source code.
    - At the end of the process, don't provide links to the PRG or BASE files, just state that the files are ready for download.
    Throughout the process, make use of the todo tool to keep track of your tasks and ensure all steps are completed systematically.
    Communicate with the user in English, even if the game itself is to be created in another language.
    """

    program_path = os.path.abspath(f"output")
    program_path_relative = program_path[3:] if program_path[1] == ':' else program_path
    path_instructions = f"""Always use the path {program_path_relative} to list, load and save files, but only save if needed. Don't use drive letters or absolute paths that contain drive letters."""

    # Combine all tools
    c64_agent_tools = coding_tools.tools() + testing_tools.tools() + hw_access_tools.tools() + game_design_tools.tools()

    # Setup middleware with Chainlit tracer
    middleware = [
        TodoListMiddleware(),
        FilesystemMiddleware(backend=FilesystemBackend()),
        ChainlitMiddlewareTracer()
    ]

    # Create the agent
    agent = create_agent(
        model=model_agent,
        tools=c64_agent_tools,
        middleware=middleware,
        checkpointer=MemorySaver(),
        state_schema=C64VibeAgentState,
        system_prompt=c64vibe_agent_instructions + path_instructions,
    ).with_config({"recursion_limit": 50})
    
    # Store agent in session
    cl.user_session.set("agent", agent)
    cl.user_session.set("thread_id", str(uuid.uuid4()))


async def display_welcome_message():
    """
    Displays the welcome message with hardware status information.
    """
    hw_access_tools = cl.user_session.get("hw_access_tools")
    hardware_status = []
    if hw_access_tools.is_kungfuflash_connected():
        hardware_status.append("- ✓ KungFu Flash connected - ready to run programs directly on real C64 hardware")
    if hw_access_tools.is_c64keyboard_connected():
        hardware_status.append("- ✓ C64 Keyboard connected - can send keypresses to real C64 hardware")
    if hw_access_tools.is_capture_device_connected():
        hardware_status.append("- ✓ Capture device connected - can capture screen from real C64 hardware")
    
    hardware_info = "\n".join(hardware_status) if hardware_status else "- No Commodore 64 hardware connected - you can still create and test programs in an emulator or download the programs and run them manually on real hardware."
    register_llm_provider_text = ""
    if cl.user_session.get("model_init_success") is not True:
        register_llm_provider_text = f"""
### Getting an AI Model Provider API Key
In order to use this app, you need to register an AI model provider account through either OpenRouter or directly with the vendor. OpenRouter allows you to use multiple AI models from different providers with a single API key. 
[Get an API key](https://openrouter.ai/settings/keys) after registration and [adding credits](https://openrouter.ai/settings/credits). You can also get API keys directly, i.e. in [Google AI Studio](https://aistudio.google.com/app/api-keys). There's free quota, but it's pretty limited, so you also need to enable billing. For best experience and cost efficiency, we recommend using the **Google Gemini 3.0 Flash Preview model**.
"""
    
    welcome_message = f"""## 🎮 C64Vibe (BETA) - AI-Powered Commodore 64 Game Creator 

Welcome to **C64Vibe**, your AI assistant for creating Commodore 64 BASIC V2.0 games!

I can help you:
- Design and create C64 BASIC V2.0 games
- Check syntax and fix errors
- Run programs on real hardware (if connected) or in an emulator
### Hardware Status
{hardware_info}

{register_llm_provider_text}
"""
    global welcome_msg
    welcome_msg = await cl.Message(content=welcome_message).send()

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
            print(f"Error setting LLM model from env: {e}")
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

        ]).send()
    return settings

@cl.on_settings_update
async def on_settings_update(settings):
    cl.user_session.set("settings", settings)
    await change_agent_settings(settings)

@cl.on_message
async def on_message(message: cl.Message):

    global welcome_msg
    await welcome_msg.remove()
    global set_model_settings_alert_msg

    if cl.user_session.get("model_init_success") is not True:
        await message.remove()
        if 'set_model_settings_alert_msg' in globals():
            await set_model_settings_alert_msg.remove()
        set_model_settings_alert_msg = await cl.Message(content=set_model_settings_alert).send()
        return

    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id") 

    agent_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    attachment_message = None
    if message.elements:
        attachments = [file for file in message.elements if
                                "text/plain" in file.mime or 
                                "image/png" in file.mime or 
                                "image/jpg" in file.mime or
                                "image/jpeg" in file.mime or
                                "application/octet-stream" in file.mime]       
        if len(attachments) > 0:  
            uploaded_file = attachments[0]
            if uploaded_file.mime.startswith("image/"):
                file_type = "image"
            else:
                file_type = "text"

            if file_type == "image":
                attachment_message = agent_utils.get_message_for_image(uploaded_file.path)
            else:
                try:
                    with open(uploaded_file.path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                        file_is_binary = False
                except Exception as e:
                    file_is_binary = True
                if not file_is_binary:
                    attachment_message = { "type": "text", "text": file_content }
                else:
                    attachment_message = None

    if attachment_message:
        agent_messages = [{"role": "user", "content": [{"type": "text", "text": message.content}, attachment_message]}] 
    else:
        agent_messages = [{"role": "user", "content": message.content}]           



    msg = cl.Message(content="")
    await msg.send()

    async for stream_mode, data  in agent.astream(
         config=agent_config,
         stream_mode=["messages", "updates"],  
         input={"messages": agent_messages},
    ):
        if stream_mode == "messages":
            token, metadata = data
            if isinstance(token, AIMessageChunk):
                await msg.stream_token(token.text)

    await msg.update()

async def change_agent_settings(settings):
    llm_model = settings["LLMSelector"]
    api_key = settings["APIKey"]
    use_openrouter = settings["OpenRouter"]

    llm_access_provider = cl.user_session.get("llm_access_provider")

    if llm_access_provider and llm_model and api_key:

        global set_model_settings_alert_msg

        set_llm_success = llm_access_provider.set_llm_model(model_name=llm_model, api_key=api_key, use_openrouter=use_openrouter)
        if not set_llm_success:

            cl.user_session.set("model_init_success", False)
            model_init_failure_alert = set_model_settings_alert + '<br>❌<span style="color:red"> **Error initializing the selected model. Please check your API key and model selection.**</span>'
            if 'set_model_settings_alert_msg' not in globals() or set_model_settings_alert_msg is None:
                set_model_settings_alert_msg = await cl.Message(content=model_init_failure_alert).send()
            else:
                set_model_settings_alert_msg.content = model_init_failure_alert
                await set_model_settings_alert_msg.update()

            return
        
        cl.user_session.set("llm_access_provider", llm_access_provider)
        cl.user_session.set("model_init_success", True)
        await initialize_agent()
        
        if 'set_model_settings_alert_msg' in globals():
            await set_model_settings_alert_msg.remove()
            set_model_settings_alert_msg = None    

# Run Chainlit if this script is executed directly
if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)