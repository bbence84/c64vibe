from rich.prompt import Prompt

model_agent = llm_access.get_gemini_model('gemini-3-pro-preview')
model_coder = llm_access.get_gemini_model('gemini-3-pro-preview')
#model_agent = llm_access.get_openai_model('gpt-4.1', azure_openai=True)



def get_user_decision(interrupts, action):
    review_configs = interrupts["review_configs"]        
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}   
    review_config = config_map[action["name"]]
    choices_str = "\n".join([f"{i+1}. {decision}" for i, decision in enumerate(review_config['allowed_decisions'])])
    user_choice = Prompt.ask("Enter your decision:  " + choices_str + "\n Pick one:", choices=[str(i+1) for i in range(len(review_config['allowed_decisions']))], show_choices=True)
    # Map back to decision value
    user_choice = review_config['allowed_decisions'][int(user_choice)-1]
    return user_choice





@tool("DesingProgramPlanDummy", description="Creates a detailed program plan for a Commodore 64 program based on a description")
def create_program_design_plan_dummy(description: str) -> str:
    return "A simple hello world program."

@tool("WriteC64CodeDummy", description="Generates C64 BASIC V2.0 source code based on a description")
def create_source_code_dummy(description: str, runtime: ToolRuntime[None, C64VibeAgentState]) -> Command:

    source_code = """10 PRINT "HELLO, WORLD!"
    20 GOTO 10
    """

    return Command(update={
        "current_source_code": source_code,
        "messages": [ToolMessage(content=f"Created source code and persisted it in the memory", tool_call_id=runtime.tool_call_id)]
    })

@tool("SyntaxCheckerDummy", description="Checks the syntax of C64 BASIC V2.0 source code")
def check_syntax_dummy(runtime: ToolRuntime[None, C64VibeAgentState]) -> str:
    current_source_code = runtime.state.get("current_source_code", "")
    print(f"Checking syntax for source code:\n{current_source_code}")
    return "No syntax errors found."

@tool("RestartC64Dummy", description="Restarts the connected Commodore 64 hardware")
def restart_c64_dummy() -> str:
    return "C64 restarted."

@tool("RunC64ProgramDummy", description="Loads and runs a C64 BASIC V2.0 program on the connected Commodore 64 hardware")
def run_c64_program_dummy() -> str:
    return "Program started on C64."

@tool("RunTestPrgOnC64", description="Sends a test PRG file to the C64 via KungFuFlash and runs it")
def run_test_prg_on_c64():
    test_prg_path = os.path.join("output", "temp_program.prg")
    with kungfuflash as kff:
        time.sleep(1)  # Wait for menu to load
        print(f"Connected to KungFuFlash on {kungfu_flash_port}")
        print(f"Sending {test_prg_path} program via USB...")
        kff.return_to_menu()
        time.sleep(4)  # Wait for menu to load
        success = kff.send_prg(test_prg_path, verbose=False)
        if success:
            print("Program sent and started successfully!")
        else:
            print("Failed to send program.")


# time.sleep(3)  # Wait for menu to load  
#run_test_prg_on_c64()
# kungfuflash.connect()
# time.sleep(3)
# kungfuflash.return_to_menu()


deepagent_middleware.append(HumanInTheLoopMiddleware(
    interrupt_on={
        "DesingProgramPlanDummy": {"allowed_decisions": ["approve", "edit", "reject"]},  
        "WriteC64CodeDummy": {"allowed_decisions": ["approve", "edit", "reject"]},
        "RestartC64Dummy": {"allowed_decisions": ["approve", "reject"]},
    }
    ))

test_agent = create_agent(
    model=model_agent,
    tools=[
        #run_test_prg_on_c64,
        run_c64_program_dummy,
        create_program_design_plan_dummy,
        create_source_code_dummy,
        check_syntax_dummy,
        restart_c64_dummy,
    ],
    checkpointer=MemorySaver(),
    state_schema=C64VibeAgentState,    
    middleware=deepagent_middleware,
    #backend=FilesystemBackend(),
    #system_prompt=f"""Run test program on the connected C64 via KungFuFlash. ALWAYS USE THE FOLDER {program_path_relative} TO LIST, LOAD AND SAVE FILES. Don't specify the drive letter.""",
    system_prompt=f"Use the write_todos tool to keep track of the progress. You can create a program design plan. Then you can create source code. Check syntax of the created code. Restart the C64 then run the program created. Use the tools as instructed. ALWAYS USE THE FOLDER {program_path_relative} TO LIST, LOAD AND SAVE FILES. Don't specify the drive letter."
)

# test_agent = create_deep_agent(
#     model=model_agent,
#     tools=[
#         #run_test_prg_on_c64,
#         run_c64_program_dummy,
#         create_program_design_plan_dummy,
#         create_source_code_dummy,
#         check_syntax_dummy,
#         restart_c64_dummy,
#     ],
#     checkpointer=MemorySaver(),
#     # interrupt_on={
#     #     "DesingProgramPlanDummy": {"allowed_decisions": ["approve", "edit", "reject"]},  
#     #     "WriteC64CodeDummy": {"allowed_decisions": ["approve", "edit", "reject"]},
#     #     "RestartC64Dummy": {"allowed_decisions": ["approve", "reject"]},
#     # },      
#     state_schema=C64VibeAgentState,    
#     backend=FilesystemBackend(),
#     #system_prompt=f"""Run test program on the connected C64 via KungFuFlash. ALWAYS USE THE FOLDER {program_path_relative} TO LIST, LOAD AND SAVE FILES. Don't specify the drive letter.""",
#     system_prompt=f"You can create a program design plan. Then you can create source code. Check syntax of the created code. Restart the C64 then run the program created. Use the tools as instructed. ALWAYS USE THE FOLDER {program_path_relative} TO LIST, LOAD AND SAVE FILES. Don't specify the drive letter."
# )


# deepagent_middleware.append(HumanInTheLoopMiddleware(
#     interrupt_on={
#         "DesingProgramPlanDummy": {"allowed_decisions": ["approve", "edit", "reject"]},  
#         "WriteC64CodeDummy": {"allowed_decisions": ["approve", "edit", "reject"]},
#         "RestartC64Dummy": {"allowed_decisions": ["approve", "reject"]},
#     }
#     ))

program_create_task = """
    Create a C64 BASIC V2.0 program that displays "HELLO, WORLD!" on the screen in a loop.
    """

#program_create_task = """Run the test program on the connected C64 via KungFuFlash."""

# Initial user request
current_input = {"messages": [{"role": "user", "content": program_create_task}]}

while True:
    interrupted = False
    last_chunk = None
    
    # Stream the agent execution
    for chunk in test_agent.stream(  
        current_input,
        stream_mode="values",
        config = agent_config,
    ): 
        last_chunk = chunk
        if "messages" in chunk:
            format_message(chunk["messages"][-1])  

        if "__interrupt__" in chunk:
            interrupted = True
            interrupts = chunk["__interrupt__"][0].value
            action_requests = interrupts["action_requests"]
            review_configs = interrupts["review_configs"]        

            # Create a lookup map from tool name to review config
            config_map = {cfg["action_name"]: cfg for cfg in review_configs}

            decisions = []
            # Display the pending actions to the user
            for action in action_requests:
                decision = get_user_decision(interrupts, action) 
                decisions.append({"type": decision})        
    
            # Resume with the user's decisions
            current_input = Command(resume={"decisions": decisions})
    
    # If there were interrupts, continue the loop to process the resumed execution
    if interrupted:
        continue
        
    # Check if the agent has actually finished (no more steps to execute)
    # If last_chunk exists and has no pending actions, we're done
    if last_chunk is not None:
        # The stream completed without interruption, agent is done
        break
    else:
        # This shouldn't happen, but if it does, exit to avoid infinite loop
        break  
