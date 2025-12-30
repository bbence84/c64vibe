import os
import time
from utils.kungfuflash_usb import KungFuFlashUSB
from dotenv import load_dotenv
load_dotenv(override=True)

try:
    kungfu_flash_port = os.getenv("KUNGFU_FLASH_PORT", "COM4")
    kungfuflash = KungFuFlashUSB(port=kungfu_flash_port)
    kungfuflash_connected = True
except Exception as e:
    print(f"Warning: Could not connect to KungFuFlash on port {kungfu_flash_port}. Continuing without KungFuFlash access.")
    kungfuflash_connected = False

for i in range(10):
    print(f"Test iteration {i+1}/10")
    with kungfuflash as kff:
        kff.return_to_menu(reconnect=True)
        time.sleep(3)  # Wait for menu to load
        success = kff.send_prg("output/temp_program.prg")
        if success:
            print("Program loaded and started on the Commodore 64 hardware.")
        else:
            print("Failed to send program to Commodore 64 hardware.")
        
    time.sleep(5)  # Wait before next iteration