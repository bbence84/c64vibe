import os
import base64
from datetime import datetime
from pydantic import BaseModel, Field
import utils.agent_utils as agent_utils
import utils.c64_syntax_checker as c64_syntax_checker

from tools.agent_state import VibeC64AgentState

from langchain.tools import tool, ToolRuntime
from typing import Annotated, Literal, NotRequired
from langgraph.types import Command
from langchain_core.messages import ToolMessage

from chainlit.utils import utc_now

LOAD_EXAMPLE_PROGRAMS = True

class CodingTools:
    def __init__(self, llm_access, cl = None, hw_access_tools = None):
        self.model_coder = llm_access.get_llm_model(create_new=True, streaming=False)
        self.llm_access = llm_access
        self.cl = cl
        self.hw_access_tools = hw_access_tools

    def tools(self):

        @tool("StoreSourceInAgentMemory", description="Stores provided C64 BASIC V2.0 source code in the agent's external memory for further processing.")
        def store_source_in_external_memory(
            runtime: ToolRuntime[None, VibeC64AgentState],
            source_code: Annotated[str, "C64 BASIC V2.0 source code to store in the agent's external memory."]
            ) -> Command:

            return Command(update={
                "current_source_code": source_code,
                "messages": [ToolMessage(content=f"Stored provided source code in the agent's external memory.", tool_call_id=runtime.tool_call_id)]
            })

        @tool("SyntaxChecker", description="Checks the syntax of C64 BASIC V2.0 source code. The source code is taken from the agent's external memory. The syntax check results are stored back in the agent's external memory.")
        def check_syntax(runtime: ToolRuntime[None, VibeC64AgentState], 
                          llm_based: Annotated[bool, "The syntax check is performed by an LLM"] = True) -> str:
            return self._check_syntax(runtime, llm_based)
                
        @tool("CreateUpdateC64BasicCode", description="Generates or updates C64 BASIC V2.0 source code based on the FULL game design description or change instructions and persists it in the agent's external memory")
        def create_source_code(
            runtime: ToolRuntime[None, VibeC64AgentState],
            game_design_description: Annotated[str, "Game design description of the program to create, including the FULL game design. Do not include code in the description, only the FULL design plan created earlier, containing all details."],
            change_instructions: Annotated[str, "Optional instructions to modify existing code. If provided, modify the existing code instead of creating new code."] = "",
            ) -> Command:
            return self._create_source_code(runtime, game_design_description, change_instructions)

        @tool("FixSyntaxErrors", description="Fixes syntax errors in C64 BASIC V2.0 source code stored in the agent's external memory or based on user-reported errors")
        def fix_syntax_errors(
                runtime: ToolRuntime[None, VibeC64AgentState],
                user_reported_errors: Annotated[str, "Optional additional information about the syntax errors reported by the user."] = "",
                ) -> Command:
            return self._fix_syntax_errors(runtime, user_reported_errors)
        
        @tool("ConvertCodeToPRG", description="Converts the C64 BASIC V2.0 source code stored in the agent's external memory to a .PRG file and offers the file for download or launching in an online C64 emulator.")
        async def convert_code_to_prg(
                game_name: Annotated[str, "Name of the game, used for naming the output .PRG file."],
                runtime: ToolRuntime[None, VibeC64AgentState]) -> str:
            return await self._convert_code_to_prg(game_name, runtime)

        return [
            check_syntax,
            create_source_code,
            fix_syntax_errors,
            convert_code_to_prg,
            store_source_in_external_memory
        ]



    def _check_syntax(self, runtime: ToolRuntime[None, VibeC64AgentState],
                    llm_based: Annotated[bool, "The syntax check is performed by an LLM"] = True) -> str:
        source_code = runtime.state.get("current_source_code", "")

        if llm_based:
            class SyntaxCheckResults(BaseModel):
                has_syntax_errors: bool = Field(description="Indicates whether there are syntax errors in the source code")
                syntax_errors: str = Field(description="List of syntax errors found in the source code, or an empty string if none were found")
            
            syntax_check_instructions = f""" Check the following C64 BASIC V2.0 source code for syntax errors:
                {source_code}
                List any syntax errors found, or state that there are no syntax errors.
                Provide only the list of syntax errors and a boolean indicating if there are syntax errors.
                Syntax errors should be described clearly with line numbers where applicable.
                """
            structured_llm_call = self.model_coder.with_structured_output(SyntaxCheckResults)  
            llm_checker_response = structured_llm_call.invoke([{"role": "user", "content": syntax_check_instructions}])

            syntax_check_output = SyntaxCheckResults.model_validate(llm_checker_response)
            syntax_check_errors = syntax_check_output.syntax_errors if syntax_check_output.has_syntax_errors else "No syntax errors found."
            if not syntax_check_output.has_syntax_errors:
                syntax_check_results = "No syntax errors found."
            else:
                syntax_check_results = "Found syntax errors."
                
        else:
            syntax_check_errors = c64_syntax_checker.check_source(source_code, return_structured=False, print_errors=False, return_warnings=False)    
        
        return Command(update={
            "syntax_errors": syntax_check_errors,
            "messages": [ToolMessage(content=f"Completed syntax check. {syntax_check_results}", tool_call_id=runtime.tool_call_id)]
        })


    def _create_source_code(self,
        runtime: ToolRuntime[None, VibeC64AgentState],
        game_design_description: Annotated[str, "Game design description of the program to create, including the FULL game design. Do not include code in the description, only the FULL design plan created earlier, containing all details."],
        change_instructions: Annotated[str, "Optional instructions to modify existing code. If provided, modify the existing code instead of creating new code."] = "",
        ) -> Command:

        load_examples = LOAD_EXAMPLE_PROGRAMS

        if change_instructions != "":

            original_code = runtime.state.get("current_source_code", "")

            code_create_instructions_1 = f"""
            Modify the following existing C64 BASIC V2.0 source code according to these instructions:
            {change_instructions}
            Original source code:
            {original_code}
            Design description of the game:
            {game_design_description}
            """
            code_create_instructions_2 = ""
            load_examples = False
        else:
            code_create_instructions_1 = f""" Generate a syntactically correct C64 BASIC V2.0 program based on the following game design description:
                {game_design_description}
                Consider all the details in the description when generating the code, i.e. players, locations, graphics, sound effects, gameplay mechanics, etc.
                Don't simplify the description, include all details in the generated code."""
            code_create_instructions_2 = f"""
                Again, the task is to generate a syntactically correct C64 BASIC V2.0 program based on the description provided earlier.
                Consider all the details in the description when generating the code, i.e. players, locations, graphics, sound effects, gameplay mechanics, etc.
                Don't simplify the description, include all details in the generated code.
                Make sure the code is ready to run on a real Commodore 64 computer without syntax errors.
                
                The game can be long and complex, so make sure to include all necessary parts to make it fully functional.

                Always add the following lines at the END of the program to state that the program has been created by the VibeC64 AI agent:
                63997 REM ==============================      
                63998 REM CREATED USING VIBEC64
                63999 REM GITHUB.COM/BBENCE84/VIBEC64
                """    
            
        code_create_instructions = f"""
            {code_create_instructions_1}
            Ensure the code adheres to C64 BASIC V2.0 syntax and conventions.
            Make sure line numbers are included and correctly ordered, and there's no duplicate line numbers.
            Provide only the source code as output, nothing else.
            C64 BASIC V2.0 has the following rules:
            - Maximum 80 characters per line, split into 2 lines (40 characters each)
            - Line numbers must be between 1 and 63999
            - Line numbers must be in increments of 10
            - Only use commands and functions available in C64 BASIC V2.0
            - No lowercase letters, only uppercase
            - No special characters outside of those supported by C64 BASIC V2.0, only use PETSCII characters.
            - Don't use accented characters, even for non-English programs.
            - Don't use pseudo control commands like {{CLR}} {{WHT}} {{DOWN}} {{DOWN}}, use CHR$() commands instead.

            In case the game contains advanced graphics or requires more perforamnce, try to use memory locations and PEEK/POKE commands to set graphics modes, colors, etc.

            {'Example BASIC V2.0 programs for reference, to follow C64 BASIC V2.0 syntax:' if load_examples else ""}
            {agent_utils.read_example_programs(num_examples=10) if load_examples else ""}
            
            {code_create_instructions_2}
            Don't use Markdown formatting, code blocks, or any additional explanations, just the pure source code text.
            """
        
        llm_coder_response = self.model_coder.invoke(
            [   {"role": "system", "content": 
                 f"""You are an expert C64 BASIC V2.0 programmer. 
                 You write syntactically correct code that runs on real Commodore 64 hardware. 
                 You consider all C64 BASIC V2.0 syntax rules and limitations. 
                 You create the code based on the user's description or change instructions."""}, 
                {"role": "user", "content": code_create_instructions}]
            )

        source_code = agent_utils.get_message_content(llm_coder_response.content)

        return Command(update={
            "current_source_code": source_code,
            "messages": [ToolMessage(content=f"Created source code based on design or change instructions and persisted it in the external memory. ", tool_call_id=runtime.tool_call_id)]
        })    

    def _fix_syntax_errors(self,
            runtime: ToolRuntime[None, VibeC64AgentState],
            user_reported_errors: Annotated[str, "Optional additional information about the syntax errors reported by the user."] = "",
            ) -> Command:
        source_code = runtime.state.get("current_source_code", "")
        syntax_errors = runtime.state.get("syntax_errors", "")
        syntax_errors += f"\nUser-reported errors: {user_reported_errors}" if user_reported_errors != "" else ""
        fix_instructions = f""" The following C64 BASIC V2.0 source code contains syntax errors:
            {source_code}
            Syntax errors identified:
            {syntax_errors}
            Provide only the corrected source code as output.
            Don't use Markdown formatting, code blocks, or any additional explanations, just the pure source code text.
            """
        llm_coder_response = self.model_coder.invoke([{"role": "user", "content": fix_instructions}])
        fixed_source_code = agent_utils.get_message_content(llm_coder_response.content)
        
        return Command(update={
            "current_source_code": fixed_source_code,
            "messages": [ToolMessage(content=f"Fixed syntax errors and updated source code in the agent's external memory.", tool_call_id=runtime.tool_call_id)]
        })  
    
    async def _convert_code_to_prg(self, game_name: str, runtime: ToolRuntime[None, VibeC64AgentState]) -> str:

        source_code = runtime.state.get("current_source_code", "")
        current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        if self.cl is None:
            temp_bas_path = os.path.join("output", f"{game_name}_{current_timestamp}.bas")
            with open(temp_bas_path, "w") as temp_bas_file:
                temp_bas_file.write(source_code)

            temp_prg_path, _ = agent_utils.convert_c64_bas_to_prg(bas_file_path=temp_bas_path, write_to_file=True)

            return f"The source code has been saved to {temp_bas_path} and converted to PRG file at {temp_prg_path}."

        else:

            # Convert the source code to a PRG file
            temp_prg_path, prg_data = agent_utils.convert_c64_bas_to_prg(bas_code=source_code, write_to_file=False)
            prg_base64 = base64.b64encode(prg_data).decode()
            props = { "button_label": "🎮 Launch Game in Online C64 Emulator",
                    "target_origin": "http://ty64.krissz.hu",
                    "prg_binary_base64": prg_base64,}     

            settings = {
                    "showEmulatorButton": True,
                    "button_label_emulator": "🎮 Launch Game in Online C64 Emulator",
                    "target_origin": "http://ty64.krissz.hu",
                    "prg_binary_base64": prg_base64,
                    "basic_source_code": source_code,
                    "showC64UButton": self.hw_access_tools.is_c64u_api_connected() if self.hw_access_tools else False,
                    "button_label_c64u": "🚀 Run program in Commodore 64 Ultimate",
                    "showKungFuButton": self.hw_access_tools.is_kungfuflash_connected() if self.hw_access_tools else False,
                    "button_label_kungfu": "🥋 Run program using KungFu Flash"
                    }               

            run_program_buttons = self.cl.CustomElement(name="RunProgramButtons", props=settings)

            elements = [
                run_program_buttons,
                self.cl.File(
                    name=f"{game_name}_{current_timestamp}.bas",
                    content=source_code,
                    display="inline",
                ),
                self.cl.File(
                    name=f"{game_name}_{current_timestamp}.prg",
                    content=prg_data,
                    display="inline",
                )
            ]

            step = self.cl.Step(name=f"ConvertGameToPRG", type="tool", elements=elements)
            step.start = utc_now()
            step.default_open = True
            step.show_input = False
            step.output = f"Converted source code to .PRG file for game '{game_name}'. Download the files below or directly launch the game in the online C64 emulator."
            step.end = utc_now()

            await step.send()   

            if temp_prg_path is None:
                return "The files have been created and are available for download or launch in the online C64 emulator."
            else:
                return f"""The files have been created and are available for download or launch in the online C64 emulator. PRG file created at path: {temp_prg_path}"""