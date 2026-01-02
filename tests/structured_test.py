import os
import base64
from datetime import datetime
import uuid
import asyncio
from pydantic import BaseModel, Field
import utils.agent_utils as agent_utils
import utils.c64_syntax_checker as c64_syntax_checker
from langchain.agents.middleware import TodoListMiddleware
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage

from tools.agent_state import C64VibeAgentState

from langchain.tools import tool, ToolRuntime
from typing import Annotated, Literal, NotRequired
from langgraph.types import Command
from langchain_core.messages import ToolMessage

from langchain.agents import create_agent

from dotenv import load_dotenv
load_dotenv()

from utils.llm_access import LLMAccessProvider
from tools.agent_state import C64VibeAgentState

llm_access_provider = LLMAccessProvider()
use_openrouter = False

model_provider = os.getenv("AI_MODEL_PROVIDER")
model_name = os.getenv("AI_MODEL_NAME")     
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

use_openrouter = False
if openrouter_api_key != "" and openrouter_api_key is not None:
    use_openrouter = True

llm_access_provider.set_llm_model(model_name_technical=model_name, model_provider=model_provider, use_openrouter=use_openrouter)
model_agent = llm_access_provider.get_llm_model()
model_coder = llm_access_provider.get_llm_model(create_new=True, streaming=False)

class SyntaxCheckResults(BaseModel):
    has_syntax_errors: bool = Field(description="Indicates whether there are syntax errors in the source code")
    syntax_errors: str = Field(description="List of syntax errors found in the source code, or an empty string if none were found")


# @tool("CheckSyntax", description="Check C64 BASIC V2.0 source code for syntax errors and return a list of any found errors.")
# def check_syntax(source_code: str, runtime: ToolRuntime[None, C64VibeAgentState]) -> Command:

#         #parser = PydanticOutputParser(pydantic_object=SyntaxCheckResults) 
#         syntax_check_instructions = f""" Check the following C64 BASIC V2.0 source code for syntax errors:
#             {source_code}
#             List any syntax errors found, or state that there are no syntax errors.
#             Provide only the list of syntax errors and a boolean indicating if there are syntax errors, in the following JSON format:
#             Syntax errors should be described clearly with line numbers where applicable.
           
#             """
#         structured_llm_call = model_coder.with_structured_output(SyntaxCheckResults)  
#         llm_checker_response = structured_llm_call.invoke([{"role": "user", "content": syntax_check_instructions}])
#         print("LLM Response:", llm_checker_response)
#         syntax_check_output = SyntaxCheckResults.model_validate(llm_checker_response)
#         syntax_check_errors = syntax_check_output.syntax_errors if syntax_check_output.has_syntax_errors else "No syntax errors found."

#         if not syntax_check_output.has_syntax_errors:
#             syntax_check_results = "No syntax errors found."
#         else:
#             syntax_check_results = "Found syntax errors."

#         return Command(update={
#             "syntax_errors": syntax_check_errors,
#             "messages": [ToolMessage(content=f"Completed syntax check. {syntax_check_results}", tool_call_id=runtime.tool_call_id)]
#         })            

# test_agent = create_agent(
#     model=model_agent,
#     tools=[
#         check_syntax
#     ],
#     state_schema=C64VibeAgentState,    
#     system_prompt=f"You are an expert C64 game programmer. You can check C64 BASIC V2.0 source code for syntax errors.",
# )    


message_start = f"""
Check syntax of:

```
1 REM TEXT ADVENTURE GAME BY CHRIS GARRETT 2024 RETROGAMECODERS.COM
2 REM SET UP VARIABLES ETC
3 GOSUB 128
4 REM SHOW ROOM DETAILS
5 GOSUB 126
6 IF PL=0 THEN PL = PP : REM PLAYER LOCATION CAN NOT BE 00 AS THAT IS INVENTORY
7 PP = PL : REM BACKUP THE LOCATION IN CASE ILLEGAL MOVE MADE
8 PRINT RV$+LO$(PL)+RO$
9 PRINT ""
10 PRINT "OBJECTS VISIBLE:"+LB$
11 FOR I = 0 TO OC-1 : REM CHECK OBJECT LOCATIONS FROM THE FIRST OBJECT TO OBJECT COUNT
12 IF OL(I) = PL THEN PRINT ". ";OB$(I) : REM IF THE OBJECT IS IN CURRENT LOCATION PRINT IT
13 NEXT I
14 PRINT ""
15 PRINT WT$+"EXITS AVAILABLE:"+LB$
16 REM CHECK EACH POSSIBLE EXIT
17 IF MID$(EX$(PL),1,2)<>"00" THEN PRINT ". NORTH"
18 IF MID$(EX$(PL),3,2)<>"00" THEN PRINT ". EAST"
19 IF MID$(EX$(PL),5,2)<>"00" THEN PRINT ". SOUTH"
20 IF MID$(EX$(PL),7,2)<>"00" THEN PRINT ". WEST"
21 IF MID$(EX$(PL),9,2)<>"00" THEN PRINT ". UP"
22 IF MID$(EX$(PL),11,2)<>"00" THEN PRINT ". DOWN"
23 I$=""
24 PRINT ""
25 PRINT YL$+"WHAT NOW?"+LB$
26 INPUT I$
27 IF LEFT$(I$,3) = "GO " THEN GOSUB 42
28 IF I$ = "N" THEN GOSUB 46
29 IF I$ = "E" THEN GOSUB 46
30 IF I$ = "S" THEN GOSUB 46
31 IF I$ = "W" THEN GOSUB 46
32 IF I$ = "U" THEN GOSUB 46
33 IF I$ = "D" THEN GOSUB 46
34 IF LEFT$(I$,1) = "I" THEN GOSUB 58
35 IF LEFT$(I$,4) = "GET " THEN GOSUB 73
36 IF LEFT$(I$,5) = "TAKE " THEN GOSUB 69
37 IF LEFT$(I$,5) = "DROP " THEN GOSUB 93
38 IF LEFT$(I$,8) = "EXAMINE " THEN GOSUB 107
39 IF LEFT$(I$,4) = "LOOK" THEN PRINT"":PRINT RD$(PL):PRINT"":GOSUB 65
40 IF LEFT$(I$,1) = "Q" THEN GOTO 190
41 GOTO 4
42 REM FULLY WRITTEN OUT MOVE (EG. GO SOUTH OR GO S)
43 D$ = MID$(I$,4,1)
44 GOSUB 50
45 RETURN
46 REM ABBREVIATED MOVE (EG. N)
47 D$ = I$
48 GOSUB 50
49 RETURN
50 REM GO TO THE NEW PLAYER LOCATION (PL)
51 IF D$ = "N" THEN PL = VAL(MID$(EX$(PL),1,2))
52 IF D$ = "E" THEN PL = VAL(MID$(EX$(PL),3,2))
53 IF D$ = "S" THEN PL = VAL(MID$(EX$(PL),5,2))
54 IF D$ = "W" THEN PL = VAL(MID$(EX$(PL),7,2))
55 IF D$ = "U" THEN PL = VAL(MID$(EX$(PL),9,2))
56 IF D$ = "D" THEN PL = VAL(MID$(EX$(PL),11,2))
57 RETURN
58 REM OBJECTS THE PLAYER IS CARRYING
59 PRINT ""
60 PRINT "OBJECTS IN YOUR POSSESSION:"
61 FOR I = 0 TO OC-1 : REM CHECK OBJECT LOCATION FROM THE FIRST OBJECT TO OBJECT COUNT
62 IF OL(I) = 0 THEN PRINT ". ";OB$(I) : REM IF THE OBJECT IS IN ZERO PRINT IT
63 NEXT I
64 PRINT ""
65 PRINT CY$+RV$+" PRESS A KEY TO CONTINUE "+RO$
66 GET I$
67 IF I$="" GOTO 66
68 RETURN
69 REM ALTERNATIVE ACTION TO GET
70 F=-1:R$=""
71 R$ = MID$(I$,6) : REM R$ IS OBJECT REQUESTED
72 GOTO 76
73 REM ALLOW PLAYER TO GET AVAILABLE OBJECT AND PUT IN INVENTORY
74 F=-1:R$=""
75 R$ = MID$(I$,5) : REM R$ IS OBJECT REQUESTED
76 REM GET THE OBJECT ID
77 FOR I = 1 TO OC
78 IF OB$(I-1) = R$ THEN F=I : REM IT EXISTS
79 NEXT I
80 REM CAN'T FIND IT?
81 PRINT ""
```
"""



agent_config = {"configurable": {"thread_id": str(uuid.uuid4())}, "recursion_limit": 50}


async def main():

    # syntax_check_instructions = f""" Check the following C64 BASIC V2.0 source code for syntax errors:
    #     {source_code}
    #     List any syntax errors found, or state that there are no syntax errors.
    #     Provide only the list of syntax errors and a boolean indicating if there are syntax errors, in the following JSON format:
    #     Syntax errors should be described clearly with line numbers where applicable.
        
    #     """
    for test_run in range(10):
        print(f"Starting syntax check run {test_run+1}...")
        structured_llm_call = model_coder.with_structured_output(SyntaxCheckResults, method='json_schema')  
        # Measure start time
        start_time = datetime.now()
        try:
            llm_checker_response = structured_llm_call.invoke([{"role": "user", "content": message_start}])
            end_time = datetime.now()
            duration = end_time - start_time
            print(f"Syntax check completed in: {duration.total_seconds()} seconds for run {test_run+1}.")

            print("LLM Response:", llm_checker_response)
            syntax_check_output = SyntaxCheckResults.model_validate(llm_checker_response)
        except Exception as e:
            print(f"Error during syntax check: {e}, for test run {test_run+1}.")
            continue
        
        syntax_check_errors = syntax_check_output.syntax_errors if syntax_check_output.has_syntax_errors else "No syntax errors found."

        if not syntax_check_output.has_syntax_errors:
            syntax_check_results = "No syntax errors found."
        else:
            syntax_check_results = "Found syntax errors."

        print(f"Completed syntax check. {syntax_check_results}")


# #def main():
#     async for stream_mode, data  in test_agent.astream(
#          config=agent_config,
#          stream_mode=["messages", "updates"],  
#          input={"messages": [{"role": "user", "content": message_start}]},
#     ):  

#         if stream_mode == "messages":
#             token, metadata = data
#             if isinstance(token, AIMessageChunk):
#                 print(token.text, end="|", flush=True)

asyncio.run(main())