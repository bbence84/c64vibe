import os

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.bas2prg import Bas2Prg

def get_message_content(content):
    """
    Extracts text content from a message which may contain text and other elements.
    """
    if len(content) == 0:
        return
    if isinstance(content, list):
        message = content[0]
    else:
        message = content
    if isinstance(message, str):
        return message
    elif isinstance(message, dict):
        return message.get("text", "")
    return str(message)   

def read_example_programs(num_examples: int = 5) -> str:
    examples = []
    example_files = os.listdir("resources/examples")
    for i, filename in enumerate(example_files):
        if i >= num_examples:
            break
        with open(os.path.join("resources/examples", filename), "r", encoding="utf-8") as f:
            content = f.read()
            examples.append(f"```basic\n{content}\n```")
    return "\n\n".join(examples)

def convert_c64_bas_to_prg(bas_file_path: str = None, bas_code: str = None, write_to_file: bool = True) -> (tuple[str, bytes]):
    prg_file_path = None
    converter = Bas2Prg()
    if bas_code is not None:
        prg_data = converter.convert(source_text=bas_code)
    else:
        prg_file_path = bas_file_path.replace(".bas", ".prg")
        prg_data = converter.convert(source_text=open(bas_file_path, "r").read())

    if write_to_file and bas_file_path is not None:
        with open(prg_file_path, "wb") as prg_file:
            prg_file.write(prg_data)

    return prg_file_path, prg_data

def format_llm_error_message(model_name: str, error_str: str) -> str:
    # Handle common error types and provide friendly English error messages
    if "RateLimitError" in error_str or "429" in error_str:
        if "quota" in error_str.lower() or "exceed" in error_str.lower():
            return f"⚠️ {model_name} API quota exceeded. Please check your plan and billing details."
        else:
            return f"⚠️ {model_name} API rate limit hit. Please try again later."
    elif "401" in error_str or "authentication" in error_str.lower():
        return f"🔑 {model_name} API key is invalid. Please check your configuration."
    elif "403" in error_str or "permission" in error_str.lower():
        return f"🚫 {model_name} API access denied. Please check permissions."
    elif "timeout" in error_str.lower():
        return f"⏰ {model_name} API call timed out. Please retry."
    else:
        return f"❌ {model_name} model call failed: {error_str}"

# if __name__ == "__main__":
#     print(get_webcam_snapshot())
# #     #convert_c64_bas_to_prg("""C:\output\guessing_game.bas""")
# #     #hardware_access = C64HardwareAccess(device_port="COM3", baud_rate=19200, debug=False)
# #     send_prg_to_c64("""C:\output\guessing_game.prg""")