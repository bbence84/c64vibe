"""Utility functions for displaying messages and prompts in Jupyter notebooks."""

from email import message
import json

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_message_content(message):
    """Convert message content to displayable string."""
    parts = []
    tool_calls_processed = False

    # Handle main content
    if isinstance(message.content, str):
        parts.append(message.content)
    elif isinstance(message.content, list):
        # Handle complex content like tool calls (Anthropic format)
        for item in message.content:
            if item.get("type") == "text":
                parts.append(item["text"])
            elif item.get("type") == "thinking":
                parts.append(f"\n💭 Thought: *{item['thinking']}*")
            elif item.get("type") == "tool_use":
                tool_name = item['name']
                tool_input = item['input']
                
                # Special handling for write_todos tool
                if tool_name == "write_todos":
                    # parts.append(f"\n🔧 Tool Call: {tool_name}")
                    # parts.append("")  # Add spacing before table
                    parts.append(format_todos(tool_input))
                    parts.append("")  # Add spacing after table
                else:
                    parts.append(f"\n🔧 Tool Call: {tool_name}")
                    parts.append(f"   Args: {json.dumps(tool_input, indent=2, ensure_ascii=False)}")
                
                #parts.append(f"   ID: {item.get('id', 'N/A')}")
                tool_calls_processed = True

    else:
        parts.append(str(message.content))

    # Handle tool calls attached to the message (OpenAI format) - only if not already processed
    if (
        not tool_calls_processed
        and hasattr(message, "tool_calls")
        and message.tool_calls
    ):
        for tool_call in message.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            # Special handling for write_todos tool
            if tool_name == "write_todos":
                # parts.append(f"\n🔧 Tool Call: {tool_name}")
                # parts.append("")  # Add spacing before table
                parts.append(format_todos(tool_args))
                parts.append("")  # Add spacing after table
            else:
                parts.append(f"\n🔧 Tool Call: {tool_name}")
                parts.append(f"   Args: {json.dumps(tool_args, indent=2, ensure_ascii=False)}")
            
            # parts.append(f"   ID: {tool_call['id']}")

    return "\n".join(parts)


def format_message(m):
    """Format and display a single message with Rich formatting."""
    msg_type = m.type
    content = format_message_content(m)

    if msg_type == "human":
        console.print(Panel(content, title="🧑 Human", border_style="blue"))
    elif msg_type == "ai":
        markdown = Markdown(content)
        console.print(Panel(markdown, title="🤖 Assistant", border_style="green"))
    elif msg_type == "tool":
        markdown = Markdown(content)
        console.print(Panel(markdown, title="🔧 Tool Output", border_style="yellow"))
    else:
        markdown = Markdown(content)
        console.print(Panel(markdown, title=f"📝 {msg_type}", border_style="white"))


def format_messages(messages):
    """Format and display a list of messages with Rich formatting."""
    for m in messages:
        format_message(m)



def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "blue"):
    """Display a prompt with rich formatting and XML tag highlighting.

    Args:
        prompt_text: The prompt string to display
        title: Title for the panel (default: "Prompt")
        border_style: Border color style (default: "blue")
    """
    # Create a formatted display of the prompt
    formatted_text = Text(prompt_text)
    formatted_text.highlight_regex(r"<[^>]+>", style="bold blue")  # Highlight XML tags
    formatted_text.highlight_regex(
        r"##[^#\n]+", style="bold magenta"
    )  # Highlight headers
    formatted_text.highlight_regex(
        r"###[^#\n]+", style="bold cyan"
    )  # Highlight sub-headers

    # Display in a panel for better presentation
    console.print(
        Panel(
            formatted_text,
            title=f"[bold green]{title}[/bold green]",
            border_style=border_style,
            padding=(1, 2),
        )
    )

# more expressive runner
async def stream_agent(agent, query, config=None):
    async for graph_name, stream_mode, event in agent.astream(
        query,
        stream_mode=["updates", "values"], 
        subgraphs=True,
        config=config
    ):
        if stream_mode == "updates":
            print(f'Graph: {graph_name if len(graph_name) > 0 else "root"}')
            
            node, result = list(event.items())[0]
            print(f'Node: {node}')
            
            for key in result.keys():
                if "messages" in key:
                    # print(f"Messages key: {key}")
                    format_messages(result[key])
                    break
        elif stream_mode == "values":
            current_state = event

    return current_state


def format_todos(todos_data):
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
    
    # Add todos to table
    for idx, todo in enumerate(todos, 1):
        status = todo.get("status", "not_started")
        content = todo.get("content", "")
        
        # Get emoji for status
        emoji = status_map.get(status, "❓")
        status_display = f"{emoji} {status.replace('_', ' ').title()}"
        
        lines.append(f"| {idx} | {status_display} | {content} |")
    
    return "\n".join(lines)
