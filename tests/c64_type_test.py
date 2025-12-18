import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.c64_hw import C64HardwareAccess

def test_type_text():
    hardware_access = C64HardwareAccess(device_port="COM3", baud_rate=19200, debug=True)
    hardware_access.restart_c64()
    import time
    time.sleep(5)  # Wait for C64 to restart
    hardware_access.type_text("PRINT \"HELLO, WORLD!\"")
    hardware_access.tap_key("Return")
    hardware_access.type_text("RUN")
    hardware_access.tap_key("Return")

if __name__ == "__main__":
    test_type_text()