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

# TODO
# -----------------------------
# ✓ Convert to web based UI
#   - Auto popup right away for setting LLM model and API key if not set
#   - Ability to upload generated bas file with a screenshot for fixing
#   - Support Hungarian language in the UI
#   - Conversation starters
#   - Registration, persisting conversations?
#   - Download also conversation summary for later upload
#   - Instructions on getting an API key on OpenRouter
#   ✓ Settings for LLM provider and model selection and API keys 
#   ✓ File download for converted created programs
#   ✓ Proper formatting of tool outputs e.g. code blocks for source code: Write file only filename, ReadFile rename, Glob?
#   ✓ Prevent full source code to end up in the main message 
#   ✓ Better welcome message with hardware status and readme.md for the UI
#   ✓ Don't save the generated prg and bas files on the server, only offer for download
#   ✓ Open generated game in an online C64 emulator directly from the UI
# - Instruction to immediately start outputting a confirmation when the agent starts
# - HIGH_PRIO Improve error handling and logging
# - HIGH_PRIO Store API keys in local storage or session storage 
# - Use structured tool outputs i.e. when generated code is returned
# - Provide examples for fancy texts for games
# - Human in the loop for approval before creating the source code
# - Check if thinking mode is better vs. non thinking mode for Gemini, check reasoning traces
# - Test case generation and execution
# - Fix file save https://github.com/langchain-ai/deepagents/pull/336
# - Clean up for open-source release
# - (PRO) Registration, persist conversations and allow loading previous sessions
# - (PRO) Sprite and graphic asset generation tools using generative AI models and convert to C64 formats
# - (PRO) Sound effect and music generation tools
# ✓ Support OpenRouter
# ✓ Extend CreateUpdateC64BasicCode tool to update existing code based on user feedback
# ✓ Pass whole game design plan to the code writing tool instead of just short description
# ✓ Implement C64 "hardware" functions (loading/running/stopping programs, sending text to screen, restarting)
# ✓ Use LangChain states for passing source code and large tool inputs / outputs in the context
# ✓ Find C64 game source codes for few shot learning
# ✓ Use Kungfu Flash or similar for program loading/running/restart?
# ✓ Camera input for screen capture
# ✓ Create library for remote C64 keyboard input
# ✓ LLM streaming response handling
# ✓ Deep agent: use the todo middleware for better step-by-step execution control
# ✓ Add LLM based syntax checking tool
# ✓ Ability to specify LLM provider and model in .env
# ✓ Check if C64 is connected, if not, fall back without hardware access  
# ✓ LangSmith based tracing and monitoring for productive deployment

import os
import uuid
import chainlit as cl
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
from tools.hw_access_tools import HWAccessTools

from dotenv import load_dotenv
load_dotenv()

set_model_settings_alert = '<span style="color:red">⚠️**Set your AI model and API key in the Settings panel (⚙️ icon in the chat input area below) before proceeding.**⚠️</span>'

@cl.on_chat_start
async def on_chat_start():
    """
    Initializes the C64Vibe agent when a chat session starts.
    """

    llm_access_provider = LLMAccessProvider()
    cl.user_session.set("llm_access_provider", llm_access_provider)

    hw_access_tools = HWAccessTools()
    cl.user_session.set("hw_access_tools", hw_access_tools)

    load_ai_model_from_env()

    await init_settings()

    await display_welcome_message(hw_access_tools)

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
    
    model_agent = llm_access_provider.get_llm_model()

    # Build agent instructions dynamically based on hardware availability
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
    c64_agent_tools = coding_tools.tools() + testing_tools.tools() + hw_access_tools.tools()

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


async def display_welcome_message(hw_access_tools):
    """
    Displays the welcome message with hardware status information.
    """
    hardware_status = []
    if hw_access_tools.is_kungfuflash_connected():
        hardware_status.append("✓ KungFu Flash connected")
    if hw_access_tools.is_c64keyboard_connected():
        hardware_status.append("✓ C64 Keyboard connected")
    if hw_access_tools.is_capture_device_connected():
        hardware_status.append("✓ Capture device connected")
    
    hardware_info = "\n".join(hardware_status) if hardware_status else "⚠ No hardware connected (emulation mode)"
    
    welcome_message = f"""# 🎮 C64Vibe - AI-Powered Commodore 64 Game Creator

Welcome to **C64Vibe**, your AI assistant for creating authentic Commodore 64 BASIC V2.0 games!

I can help you:
- Design and create C64 BASIC V2.0 games
- Check syntax and fix errors
- Run programs on real hardware (if connected)
- Capture and analyze C64 screen output

Check the readme (top right corner icon) for more details.

**Hardware Status:**
{hardware_info}

What game would you like to create today?"""
    global welcome_msg
    welcome_msg = await cl.Message(content=welcome_message).send()

def load_ai_model_from_env():
    model_provider = os.getenv("AI_MODEL_PROVIDER")
    model_name = os.getenv("AI_MODEL_NAME")     
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    if model_provider and model_name:
        cl.user_session.set("llm_model", model_name)
        cl.user_session.set("model_provider", model_provider)
        cl.user_session.set("openrouter_api_key", openrouter_api_key)

        use_openrouter = False
        if openrouter_api_key != "" and openrouter_api_key is not None:
            use_openrouter = True
        
        llm_access_provider = cl.user_session.get("llm_access_provider")
        try:
            llm_access_provider.set_llm_model(model_name_technical=model_name, model_provider=model_provider, use_openrouter=use_openrouter)
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
                values=["Google Gemini 3.0 Flash Preview", "Google Gemini 3.0 Pro","Anthropic Claude 4.5 Sonnet", "Anthropic Claude 4.5 Opus", "OpenAI GPT-5", "OpenAI GPT-5.2"],
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

async def change_agent_settings(settings):
    # Condition for LLMModel
    llm_model = settings["LLMSelector"]
    api_key = settings["APIKey"]
    use_openrouter = settings["OpenRouter"]

    cl.user_session.set("llm_model", llm_model)
    cl.user_session.set("api_key", api_key)
    cl.user_session.set("use_openrouter", use_openrouter)

    print(f"Selected LLM Model: {llm_model}")
    print(f"API Key: {api_key}")
    print(f"Use OpenRouter: {use_openrouter}")

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

@cl.on_message
async def on_message(message: cl.Message):
    """
    Handles incoming user messages and streams agent responses.
    """

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

    # if message.elements:
    #     print(message.elements)
    #     attachments = [file for file in message.elements]
    #     if len(attachments) > 0:  
    #         uploaded_file = attachments[0]
    #         # Check if file extensions is .bas or .BAS
    #         if uploaded_file.name.lower().endswith(".bas"):
    #             with open(uploaded_file.path, "r") as f:
    #                 file_content = f.read()
    #                 file_path = uploaded_file.path
    #             await cl.Message(content=f"Uploaded C64 BASIC source code file: {uploaded_file.name}").send()


    agent_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    msg = cl.Message(content="")
    await msg.send()

    async for stream_mode, data  in agent.astream(
         config=agent_config,
         stream_mode=["messages", "updates"],  
         input={"messages": [{"role": "user", "content": message.content}]},
    ):
        if stream_mode == "messages":
            token, metadata = data
            if isinstance(token, AIMessageChunk):
                await msg.stream_token(token.text)

    # Stream agent responses
    # async for event in agent.astream_events(
    #     config=agent_config,
    #     input={"messages": [{"role": "user", "content": message.content}]},
    #     version="v2"
    # ):
    #     if event["event"] == "on_chat_model_stream":
    #         chunk = event.get("data", {}).get("chunk")
    #         if chunk and hasattr(chunk, "content"):
    #             await msg.stream_token(agent_utils.get_message_content(chunk.content))
                # if len(chunk.content) == 0:
                #     continue
                # # Check if chunk.content is a list
                # if isinstance(chunk.content, list):
                #     last_message = chunk.content[-1]
                # else:
                #     last_message = chunk.content
                # if last_message:
                #     # Check if last_message is a str 
                #     if isinstance(last_message, str):
                #         await msg.stream_token(last_message)
                #     elif isinstance(last_message, dict):
                #         await msg.stream_token(last_message.get("text", ""))

    await msg.update()

# Run Chainlit if this script is executed directly
if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)