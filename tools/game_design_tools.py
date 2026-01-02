from langchain.tools import tool, ToolRuntime
from typing import Annotated, Literal, NotRequired
import utils.agent_utils as agent_utils

from tools.agent_state import C64VibeAgentState

class GameDesignTools:
    def __init__(self, llm_access, capture_device_connected=False):
        self.model_coder = llm_access.get_llm_model(create_new=True, streaming=False)

    def tools(self):

        @tool("DesignGamePlan", description="Creates a detailed game design plan for a Commodore 64 game based on a description")
        def create_game_design_plan(description: Annotated[str, "Description of the game to design. Just the description provided by the user."]) -> str:
            return self._create_game_design_plan(description)

        tools = []
        tools.append(create_game_design_plan)

        return tools

    def _create_game_design_plan(self, description: str) -> str:
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
            The design plan should not contain any code, only the design details.
            The design plan should consider the technical limitations of the Commodore 64, including graphics, sound, and memory constraints.
            """
        llm_design_response = self.model_coder.invoke([{"role": "user", "content": design_instructions}])
        return agent_utils.get_message_content(llm_design_response.content)


