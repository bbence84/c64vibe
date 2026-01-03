from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.load.dump import dumps
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from collections.abc import Callable

from chainlit.context import context_var
from chainlit.step import Step
from chainlit.utils import utc_now
import chainlit as cl
import logging

from typing import Any
from typing import cast

logger = logging.getLogger(__name__)

class ChainlitMiddlewareTracer(AgentMiddleware if AgentMiddleware != object else object):
    """
    Middleware tracer for LangChain v1.x agents integrating with Chainlit.

    This middleware tracks tool calls and displays them as steps in the
    Chainlit UI, providing real-time visibility into agent execution.

    Features:
    - Tracks tool invocations as Chainlit Steps
    - Shows tool inputs and outputs
    - Handles errors gracefully
    - Works with LangGraph agents
    """

    def __init__(self):
        if AgentMiddleware != object:
            super().__init__()
        self.active_steps: dict[str, Step] = {}
        self.parent_step_id: str | None = None

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ):
        """
        Wrap tool calls to track them in Chainlit UI.

        Args:
            request: The tool call request
            handler: The tool execution handler

        Returns:
            The tool execution result
        """
        tool_name = request.tool_call["name"]
        tool_input = request.tool_call["args"]

        if tool_name == "write_todos": tool_name = "WriteTodos"
        if tool_name == "write_file": tool_name = "WriteFile"
        if tool_name == "read_file": tool_name = "ReadFile"
        if tool_name == "edit_file": tool_name = "EditFile"
        if tool_name == "glob": tool_name = "FindFiles"
        if tool_name == "ls": tool_name = "GetFileList"

        # Create a step for this tool call

        if tool_name != "ConvertCodeToPRG":
                
            step = Step(name=tool_name, type="tool")
            step.start = utc_now()

            # Format the tool input
            try:
                step.input, _, step.show_input  = self._format_input(tool_name, tool_input)
                #step.input, step.language = self._process_content(tool_input)
                #step.show_input = step.language or False
            except Exception as e:
                logger.error(f"Error formatting tool input for Chainlit: {e}")
                step.input = str(tool_input)
                step.show_input = True

            await step.send()

        # Execute the tool
        try:
            result = await handler(request)

            if tool_name == "ConvertCodeToPRG":
                return result
            
            # Format the output
            try:
                #step.output, step.language = self._process_content(result.content)
                tool_formatted_output, text_language = await self._format_output(tool_name, result)
                if text_language == "basic":
                    tool_formatted_output = f"```basic\n{tool_formatted_output}\n```"
                step.output = tool_formatted_output
            except Exception as e:
                logger.error(f"Error formatting tool output for Chainlit: {e}, tool_name: {tool_name}, result: {result}")
                step.output = str(result)

            step.end = utc_now()
            await step.update()

            return result

        except Exception as e:
            # Mark step as error
            step.is_error = True
            step.output = str(e)
            step.end = utc_now()
            await step.update()
            raise
    
    async def _format_output(self, tool_name: str, tool_output: Any) -> tuple[dict | str, str | None]:
        """
        Format tool output for display in Chainlit.

        Args:
            tool_output: The tool output to format

        Returns:
            Tuple of (formatted output, language hint)
        """
        if tool_output is None:
            return {}, None
        
        match tool_name:
            case "DesignGamePlan":
                return tool_output.content, "markdown"
            case "WriteTodos":
                tool_command = cast(Command, tool_output)
                return await self._format_todos(tool_command.update.get("todos", [])), "markdown"
            case "CreateUpdateC64BasicCode" | "StoreSourceInAgentMemory":
                tool_command = cast(Command, tool_output)
                return tool_command.update.get("current_source_code", ""), "basic"
            case "SyntaxChecker":
                tool_command = cast(Command, tool_output)
                return tool_command.update.get("syntax_errors", ""), "markdown"
            case "FixSyntaxErrors":
                tool_command = cast(Command, tool_output)
                return tool_command.update.get("current_source_code", ""), "basic"
            case "RunC64Program":
                return tool_output.content, "markdown"
            # case "WriteFile":
            #     tool_command = cast(Command, tool_output)
            #     return f"File '{tool_command.update.get('filename', '')}' written successfully.", None
            case _:
                return self._process_content(tool_output.content)

    def _format_input(self, tool_name: str, tool_input: Any) -> tuple[dict | str, str | None, bool]:
        """
        Format tool input for display in Chainlit.

        Args:
            tool_input: The tool input to format

        Returns:
            Tuple of (formatted input, language hint, show_input flag)
        """
        if tool_input is None:
            return {}, None, False
        
        match tool_name:
            case "CreateUpdateC64BasicCode":
                game_design_description = tool_input.get("game_design_description", "")
                change_instructions = tool_input.get("change_instructions", "")
                if change_instructions != "":
                    return change_instructions, "text", True
                else:
                    return game_design_description, "text", True
            case "RunC64Program":
                return "", "text", False
            case "DesignGamePlan":
                return tool_input.get("description", ""), "text", True
            case "StoreSourceInAgentMemory":
                return "", "text", False
            case "SyntaxChecker" | "WriteTodos":
                return "", "text", False
            case "FixSyntaxErrors":
                user_reported_errors = tool_input.get("user_reported_errors", "")
                if user_reported_errors != "":                
                    return user_reported_errors, "text", True    
                else:
                    return "", "text", False        
            case "WriteFile" | "ReadFile" | "EditFile" | "FindFiles" | "GetFileList":
                return "", "text", False
            case _:
                return self._process_content(tool_input) + (True,)
            

    async def _format_todos(self, todos_data):
        """Format and display a todo list as a markdown table.
        
        Args:
            todos_data: Either a dict with 'todos' key or a list of todo items
                    Each todo should have 'status' and 'content' keys
        
        Returns:
            str: Markdown formatted table string
        """
        # Handle both dict and list formats
        if isinstance(todos_data, dict) and "todos" in todos_data:
            todos = todos_data["todos"]
        elif isinstance(todos_data, list):
            todos = todos_data
        else:
            return "**Invalid todo format**"
        
        # Status emoji mapping
        status_map = {
            "completed": "✅",
            "in_progress": "🔄",
            "not_started": "⏸️",
            "pending": "⏸️",
            "blocked": "🚫",
        }
        
        # Build markdown table
        lines = [
            "### 📋 Todo List",
            "",
            "| # | Status | Task |",
            "|--:|:------|:-----|"
        ]

        task_list = cl.TaskList()
        task_list.status = "Running..."
        cl.user_session.set("task_list", task_list)
        
        # Add todos to table
        for idx, todo in enumerate(todos, 1):
            status = todo.get("status", "not_started")
            content = todo.get("content", "")
            
            # Get emoji for status
            emoji = status_map.get(status, "❓")
            status_display = f"{emoji} {status.replace('_', ' ').title()}"
            
            lines.append(f"| {idx} | {status_display} | {content} |")

            match status:
                case "completed":
                    task_status = cl.TaskStatus.DONE
                case "in_progress":
                    task_status = cl.TaskStatus.RUNNING
                case "not_started" | "pending":
                    task_status = cl.TaskStatus.READY
                case "blocked":
                    task_status = cl.TaskStatus.FAILED
                case _:
                    task_status = cl.TaskStatus.READY      

            task = cl.Task(title=content, status=task_status)
            await task_list.add_task(task)       

        await task_list.send()     
        
        return "\n".join(lines)


    def _process_content(self, content: Any) -> tuple[dict | str, str | None]:
        """
        Process content for display in Chainlit.

        Args:
            content: The content to process

        Returns:
            Tuple of (formatted content, language hint)
        """
        if content is None:
            return {}, None
        if isinstance(content, str):
            return {"content": content}, "json"
        else:
            return dumps(content), "json"