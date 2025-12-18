from deepagents.middleware.subagents import SubAgent
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from typing import Annotated
import utils.c64_syntax_checker as c64

llm = init_chat_model('gpt-4.1', model_provider="azure_openai") # Uses Azure OpenAI

@tool("SyntaxChecker", description="Checks the syntax of C64 BASIC V2.0 source code")
def check_syntax(source_code: Annotated[str, "The source code to check"]) -> str:
    print("Checking syntax for source code")
    return c64.check_source(source_code, return_structured=False, print_errors=True)    

@tool("WriteC64SourceCode", description="Generates C64 BASIC V2.0 source code based on a description")
def create_source_code(description: Annotated[str, "Description of the program to create"]) -> str:
    print("Generating C64 BASIC V2.0 source code")
    # Placeholder implementation - in a real scenario, this would generate code based on the description
    code_create_instructions = f""" Generate a syntactically correct C64 BASIC V2.0 program based on the following description:
        {description}
        Ensure the code adheres to C64 BASIC V2.0 syntax and conventions.
        Provide only the source code as output.
        """
    llm_response = llm.invoke([{"role": "user", "content": code_create_instructions}])
    return llm_response.content

@tool("FixSyntaxErrors", description="Fixes syntax errors in C64 BASIC V2.0 source code")
def fix_syntax_errors(
        source_code: Annotated[str, "C64 BASIC V2.0 source code with potential syntax errors"],
        syntax_errors: Annotated[str, "Description of the syntax errors identified in the source code"]) -> str:
    print("Fixing syntax errors in source code")
    fix_instructions = f""" The following C64 BASIC V2.0 source code contains syntax errors:
        {source_code}
        Syntax errors identified:
        {syntax_errors}
        Provide only the corrected source code as output.
        """
    llm_response = llm.invoke([{"role": "user", "content": fix_instructions}])
    return llm_response.content

coding_subagent = SubAgent(
    name="C64 BASIC V2.0 Coding and Syntax Checker Assistant",
    description="Writes syntactically correct C64 BASIC V2.0 code based on descriptions and checks the syntax.",
    system_prompt="""
        You are an expert C64 BASIC V2.0 code generator and syntax checker.
        Given a description of a program, you will generate C64 BASIC V2.0 code using the CreateSourceCode tool, a code that is syntactically correct.
        After generating the code, you will use the provided syntax checking tool SyntaxChecker to ensure there are no syntax errors.
        If there are syntax errors, you correct them using the FixSyntaxErrors tool and re-check them using the SyntaxChecker tool until the code is error-free.
        Finally, you will return the syntactically correct C64 BASIC V2.0 source code only after all syntax errors have been resolved.
    """,
    tools=[
        check_syntax,
        create_source_code,
        fix_syntax_errors
    ],
)