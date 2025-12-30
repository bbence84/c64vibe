from typing import NotRequired
from langchain.agents import AgentState

class C64VibeAgentState(AgentState):
    current_source_code: NotRequired[str]
    syntax_errors: NotRequired[str]  