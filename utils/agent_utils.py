from datetime import datetime
import logging
import os

import sys
from pathlib import Path

logger = logging.getLogger(__name__)

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

def read_example_programs(num_examples: int = 5, folder: str = "resources/examples_c64basic") -> str:
    # Only read the *.bas files from the folder and not the subfolders
    examples = []
    example_files = [f for f in os.listdir(folder) if f.endswith(".bas") and os.path.isfile(os.path.join(folder, f))]
    for i, filename in enumerate(example_files):
        if i >= num_examples:
            break
        with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
            content = f.read()
            examples.append(f"```basic\n{content}\n```")
            logger.info(f"Loaded example program from {filename}")
    return "\n\n".join(examples)

def convert_c64_bas_to_prg(bas_code: str, write_to_file: bool = True, xcbasic3_mode = False) -> (tuple[str, bytes, str]):
    prg_file_path = None

    if xcbasic3_mode:

        current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_bas_path = os.path.join("output", f"tmp_{current_timestamp}.bas")
        with open(temp_bas_path, "w") as temp_bas_file:
            temp_bas_file.write(bas_code)

        prg_file_path = os.path.join("output", f"tmp_{current_timestamp}.prg")

        import subprocess
        result = subprocess.run(['xcbasic3', temp_bas_path, prg_file_path], capture_output=True, text=True)
        conversion_output = ''

        if result.returncode != 0:
            err_output = result.stderr
            if ': syntax error near ' in err_output:
                err_output = err_output.split(':')[2]
                import re
                err_output = re.sub(r'in file .* in line (\d+)', r'at line \1', err_output).strip()


            conversion_output = 'Error in source code:\n' + err_output
            return prg_file_path, b'', conversion_output
        else:
            conversion_output = 'Successfully converted source code to PRG file.'
            # Read the generated PRG file
            with open(prg_file_path, "rb") as prg_file:
                prg_data = prg_file.read()
        
            return prg_file_path, prg_data, conversion_output

    else:

        converter = Bas2Prg()
        prg_data = converter.convert(source_text=bas_code)

        if write_to_file:
            current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            prg_file_path = os.path.join("output", f"tmp_{current_timestamp}.prg")
            with open(prg_file_path, "wb") as prg_file:
                prg_file.write(prg_data)

        return prg_file_path, prg_data, "Successfully converted source code to PRG file."

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

if __name__ == "__main__":
    source_code = """
POKE 53280, 0 : POKE 53281, 0
POKE 646, 1
SYS $E544

DIM x AS BYTE : x = 14
DIM y AS BYTE : y = 12
DIM dx AS BYTE : dx = 1
DIM dy AS BYTE : dy = 1
DIM k$ AS STRING * 1
DIM old_x AS BYTE
DIM old_y AS BYTE

CONST SCREEN_RAM = 1024
CONST MSG = "HELLO WORLD"
CONST MSG_LEN = 11
CONST MAX_X = 29
CONST MAX_Y = 24


SUB DRAW_MSG(px AS BYTE, py AS BYTE, mode AS BYTE) STATIC
    DIM addr AS WORD
    DIM i AS BYTE
    addr = SCREEN_RAM + CWORD(py) * 40 + CWORD(px)
    FOR i = 0 TO 10
        IF mode = 1 THEN
            POKE addr + i, ASC(MID$(MSG, i + 1, 1))
        ELSE
            POKE addr + i, 32
        END IF
    NEXT
END SUB

MAIN_LOOP:
    old_x = x
    old_y = y

    IF x + dx > MAX_X OR x + dx > 250 THEN
        dx = 255
    ELSEIF x + dx = 0 THEN
        dx = 1
    END IF

    IF y + dy > MAX_Y OR y + dy > 250 THEN
        dy = 255
    ELSEIF y + dy = 0 THEN
        dy = 1
    END IF

    x = x + dx
    y = y + dy

    CALL DRAW_MSG(old_x, old_y, 0)
    CALL DRAW_MSG(x, y, 1)

    FOR t = 0 TO 50 : NEXT t

    GET k$
    IF k$ = "" THEN GOTO MAIN_LOOP

END

REM ==============================
REM CREATED USING VIBEC64 IN XC=BASIC
REM GITHUB.COM/BBENCE84/VIBEC64
"""


    prg_file_path, prg_data, conversion_output = convert_c64_bas_to_prg(source_code, xcbasic3_mode=True)
    print(conversion_output)
# #     #hardware_access = C64HardwareAccess(device_port="COM3", baud_rate=19200, debug=False)
# #     send_prg_to_c64("""C:\output\guessing_game.prg""")