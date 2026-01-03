import os
import time
import logging
from typing_extensions import runtime

from utils.c64_hw import C64HardwareAccess
from utils.kungfuflash_usb import KungFuFlashUSB
import utils.agent_utils as agent_utils
from tools.agent_state import C64VibeAgentState
from langchain.tools import tool, ToolRuntime

logger = logging.getLogger(__name__)

class HWAccessTools:
    def __init__(self):
        self._init_kungfu_flash()
        self._init_c64_keyboard()
        self.capture_device_connected = False

    def is_capture_device_connected(self):
        return self.capture_device_connected

    def is_c64keyboard_connected(self):
        return self.c64keyboard_connected

    def is_kungfuflash_connected(self):
        return self.kungfuflash_connected

    def _init_c64_keyboard(self):
        try:
            keyboard_port = os.getenv("C64_KEYBOARD_DEVICE_PORT", "COM3")
            self.c64keyboard = C64HardwareAccess(device_port=keyboard_port, baud_rate=19200, debug=False)
            self.c64keyboard_connected = True
        except Exception as e:
            logger.warning(f"Could not connect to C64 keyboard hardware on port {keyboard_port}. Continuing without keyboard access.")
            self.c64keyboard_connected = False

    def _init_kungfu_flash(self):
        try:
            kungfu_flash_port = os.getenv("KUNGFU_FLASH_PORT", "COM4")
            self.kungfuflash = KungFuFlashUSB(port=kungfu_flash_port)
            self.kungfuflash_connected = True
        except Exception as e:
            logger.warning(f"Could not connect to KungFuFlash on port {kungfu_flash_port}. Continuing without KungFuFlash access.")
            self.kungfuflash_connected = False

    def tools(self):

        @tool("RunC64Program", description="Loads and runs the C64 BASIC V2.0 program from the agent's external memory on the connected Commodore 64 hardware")
        def run_c64_program(runtime: ToolRuntime[None, C64VibeAgentState]) -> str:
            return self._run_c64_program(runtime)
        
        @tool("RestartC64", description="Restarts the connected Commodore 64 hardware")
        def restart_c64(runtime: ToolRuntime[None, C64VibeAgentState]) -> str:
            return self._restart_c64()
        
        tools = []

        if self.is_c64keyboard_connected():
            tools.append(restart_c64)
        
        if self.is_kungfuflash_connected():
            tools.append(run_c64_program)
            
        return tools
    
    # def _download_c64_program(self, game_name: str, runtime: ToolRuntime[None, C64VibeAgentState]) -> str:
    #     # Write the source code to a temporary BAS file
    #     source_code = runtime.state.get("current_source_code", "")
    #     temp_bas_path = os.path.join("output", f"{game_name}.bas")
    #     with open(temp_bas_path, "w") as temp_bas_file:
    #         temp_bas_file.write(source_code)
        
    #     # Convert the source code to a PRG file
    #     temp_prg_path = agent_utils.convert_c64_bas_to_prg(temp_bas_path)
    #     return temp_prg_path, temp_bas_file
    
    
    def _run_c64_program(self, runtime: ToolRuntime[None, C64VibeAgentState]) -> str:

        source_code = runtime.state.get("current_source_code", "")

        if not self.kungfuflash_connected:
            return "Error: KungFuFlash hardware not connected. Cannot run program on Commodore 64."

        # Write / overwrite the source code to a temporary PRG file
        temp_bas_path = os.path.join("output", "temp_program.bas")
        with open(temp_bas_path, "w") as temp_bas_file:
            temp_bas_file.write(source_code)
        
        # Convert the source code to a PRG file
        temp_prg_path, _ = agent_utils.convert_c64_bas_to_prg(bas_file_path=temp_bas_path, write_to_file=True)

        with self.kungfuflash as kff:
            kff.return_to_menu(reconnect=True)
            time.sleep(3)  # Wait for menu to load
            # print(f"Connected to KungFuFlash on {kff.get_port()}")
            # print(f"Sending {temp_prg_path} program via USB...")
            success = kff.send_prg(temp_prg_path)
            if success:
                return "Program loaded and started on the Commodore 64 hardware."
            else:
                return "Failed to send program to Commodore 64 hardware."
        
    def _restart_c64(self):
        self.c64keyboard.restart_c64()
        return "Commodore 64 restarted."    


# @tool("RunC64Program", description="Loads and runs a C64 BASIC V2.0 program on the connected Commodore 64 hardware")
# def run_c64_program(source_code: str) -> str:
#     c64hw.run_program_from_text(source_code, restart_c64=True)
#     return "Program loaded and started on the Commodore 64 hardware."
