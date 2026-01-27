import os
import time
import logging
import asyncio
from typing import Annotated, Literal, NotRequired
from typing_extensions import runtime

from utils.kungfuflash_usb import KungFuFlashUSB
from utils.c64u_api import C64UApiClient

import utils.agent_utils as agent_utils
from tools.agent_state import VibeC64AgentState
from langchain.tools import tool, ToolRuntime

logger = logging.getLogger(__name__)

class HWAccessTools:
    def __init__(self):
        self._init_kungfu_flash()
        self._init_c64u_api()

    def is_kungfuflash_connected(self):
        return self.kungfuflash_connected

    def is_c64u_api_connected(self):
        return self.c64u_api_connected
    
    def _init_c64u_api(self):
        try:
            self.c64u_api_base = os.getenv("C64U_API_BASE_URL")
            if self.c64u_api_base is None or self.c64u_api_base.strip() == "":
                self.c64u_api_connected = False
                return

            async def check_api():
                async with C64UApiClient(self.c64u_api_base) as api:
                    is_connected = await api.check_c64_api()
                    return is_connected

            self.c64u_api_connected = asyncio.run(check_api())
        except Exception as e:
            logger.warning(f"Could not connect to C64U API at {self.c64u_api_base}. Continuing without C64U API access.")
            self.c64u_api_connected = False

    def _init_kungfu_flash(self):
        try:
            kungfu_flash_port = os.getenv("KUNGFU_FLASH_PORT")
            if kungfu_flash_port is None or kungfu_flash_port.strip() == "":
                self.kungfuflash_connected = False
                return
            self.kungfuflash = KungFuFlashUSB(port=kungfu_flash_port)
            self.kungfuflash_connected = True
        except Exception as e:
            logger.warning(f"Could not connect to KungFuFlash on port {kungfu_flash_port}. Continuing without KungFuFlash access.")
            self.kungfuflash_connected = False

    def tools(self):

        @tool("RunC64Program", description="Loads and runs the C64 program from the agent's external memory on the connected Commodore 64 hardware")
        def run_c64_program(runtime: ToolRuntime[None, VibeC64AgentState]) -> str:
            source_code = runtime.state.get("current_source_code", "")
            if self.is_c64u_api_connected():
                return self.run_c64_program_c64u_api(source_code)
            elif self.is_kungfuflash_connected():
                return self.run_c64_program_kungfu(source_code)
            else:
                return "Error: No compatible hardware connected to run the C64 program."
        
        tools = []
        
        if self.is_kungfuflash_connected() or self.is_c64u_api_connected():
            tools.append(run_c64_program)           
            
        return tools
        
    def run_c64_program_c64u_api(self, source_code: str) -> str:
        

        if not self.c64u_api_connected:
            return "Error: C64U API hardware not connected. Cannot run program on Commodore 64."
        
        # Convert the source code to a PRG file
        _, prg_data, _ = agent_utils.convert_c64_bas_to_prg(bas_code=source_code, write_to_file=True)

        async def run_prg_via_api():
            async with C64UApiClient(self.c64u_api_base) as api:
                response = await api.reset_machine_soft()
                time.sleep(4)  # Wait for reset to complete
                response = await api.run_prg_binary(prg_data)
                return response

        response = asyncio.run(run_prg_via_api())

        if "errors" in response:
            return f"Error running program via C64U API: {response['errors']}"

        return "Program loaded and started on the Commodore 64 Ultimate"
    
    def run_c64_program_kungfu(self, source_code: str) -> str:

        if not self.kungfuflash_connected:
            return "Error: KungFuFlash hardware not connected. Cannot run program on Commodore 64."
        
        # Convert the source code to a PRG file
        temp_prg_path, _, _ = agent_utils.convert_c64_bas_to_prg(bas_code=source_code, write_to_file=True)

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
        
