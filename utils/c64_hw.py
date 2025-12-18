import time
import serial
try:
    from utils.c64_keymaps import rawKeys, defaultMap
except ModuleNotFoundError:
    from c64_keymaps import rawKeys, defaultMap

KEYPRESS_DELAY = 0.15  # seconds

class C64HardwareAccess:
    def __init__(self, device_port, baud_rate=19200, debug=False):
        self.device_port = device_port
        self.baud_rate = baud_rate
        self.debug = debug
        self.arduino = None

        try:
            self.arduino = serial.Serial(self.device_port, self.baud_rate, timeout=.1)
            # Give serial interface time to settle down
            time.sleep(1)
        except Exception as e:
            if self.debug:
                print(f"Cannot open serial device: {e}")
            raise e

    def tap_key(self, key_name):
        combined = ''
        if '+' in key_name and len(key_name) > 1:
            parts = key_name.split('+')
            mapped_parts = []
            for part in parts:
                if part in rawKeys:
                    mapped_parts.append(','.join(list(rawKeys[part])))
            
            if mapped_parts:
                combined = '_'.join(mapped_parts)
                if self.debug:
                    print(f"Combined key '{key_name}' to '{combined}'")
        else:
            if key_name in rawKeys:
                combined = ','.join(list(rawKeys[key_name]))
                if self.debug:
                    print(f"Key '{key_name}' mapped to '{combined}'")
        
        if combined:
            self.send_command(combined)

    def type_text(self, text):
        for char in text:
            if char in rawKeys:
                if self.debug:
                    print(f"Typing character '{char}', ascii: {ord(char)} using raw key mapping")
                self.tap_key(char)            
            elif ord(char) in defaultMap:
                key_mapping = defaultMap[ord(char)]
                if self.debug:
                    print(f"Typing character '{char}', ascii: {ord(char)} using mapping '{key_mapping}'")
                self.tap_key(key_mapping)
            else:
                print(f"Warning: Character '{char}' (ord {ord(char)}) not found in keymaps.")

    def send_command(self, command_string):
        self.arduino.write((command_string + '\n').encode())
        time.sleep(KEYPRESS_DELAY)  # Delay to allow C64 to process the command

    def close(self):
        if self.arduino and self.arduino.is_open:
            self.arduino.close()

    def quit_from_program(self):
        self.tap_key("Return")
        self.tap_key("Run/Stop")

    def restart_c64(self):
        self.tap_key("Return")
        self.type_text("SYS64738")
        self.tap_key("Return")
        time.sleep(3)  # Wait for C64 to restart

    def run_program_from_text(self, program_text, restart_c64=True):
        if restart_c64:
            self.restart_c64()
            time.sleep(4)  # Wait for C64 to restart
        lines = program_text.splitlines()
        self.tap_key("Return")
        line_counter = 0
        for line in lines:
            line_counter += 1
            line = line.rstrip('\n').rstrip('\r')
            print(f"Typing ({line_counter}/{len(lines)}): {line}")
            self.type_text(line)
            self.tap_key("Return")
        self.type_text("RUN")
        self.tap_key("Return")

    def load_and_run_program(self, file_path, run_after_load=True):
        with open(file_path, "r") as f:
            lines = f.readlines()
        
        self.quit_from_program()
        self.type_text("NEW")
        self.tap_key("Return")
        line_counter = 0
        for line in lines:
            line_counter += 1
            line = line.rstrip('\n').rstrip('\r')
            print(f"Typing ({line_counter}/{len(lines)}): {line}")
            self.type_text(line)
            self.tap_key("Return")

        if run_after_load:
            self.type_text("RUN")
            self.tap_key("Return")

    def list_program(self):
        self.tap_key("Return")
        self.type_text("LIST")
        self.tap_key("Return")  

if __name__ == "__main__":

    try:
        hardware_access = C64HardwareAccess(device_port="COM3", baud_rate=19200, debug=False)

        #hardware_access.tap_key("Return")
        #hardware_access.type_text("HKS")
        # hardware_access.tap_key("Return") 
        #hardware_access.restart_c64()
        # hardware_access.tap_key("Return")
        # hardware_access.type_text("===$$$...   ... ZZZ")
        # hardware_access.tap_key("Return")
                
        #load_and_run_program(f"source_code/guess_hun.bas", run_after_load=True)
        #hardware_access.restart_c64()
        #time.sleep(4)  # Wait for C64 to restart
        # hardware_access.tap_key("Return")
        # hardware_access.restart_c64()
        #hardware_access.load_and_run_program(f"../resources/examples/word.bas", run_after_load=True)
        #hardware_access.quit_from_program()

        # hardware_access.type_text("9200 DATA 255,255,255,255,255,255,255,255,255,99,0,0")
        #hardware_access.load_and_run_program(f"../resources/examples/invaders.bas", run_after_load=True)
        #hardware_access.type_text("LIST 8015-8052")
        #hardware_access.tap_key("Return")

        # #hardware_access.list_program()
        for _ in range(200):
            #hardware_access.type_text(f"""= ! % / ' # & ( ) , - . ; :""")
            hardware_access.tap_key("Return")
            hardware_access.type_text(f"""! % ;== NN 123 4 5""")
            #hardware_access.tap_key("=")
            #hardware_access.tap_key("Return")
            time.sleep(0.5)

        #hardware_access.type_text("N")
        #hardware_access.tap_key("Return")
        # hardware_access.type_text("59")
        # hardware_access.tap_key("Return")

        #hardware_access.tap_key("+")

        #hardware_access.tap_key("Return")
        # List lines from 10 to 500
        # hardware_access.type_text("LIST 100-1000")
        # hardware_access.tap_key("Return")

        #BCM
        # #hardware_access.type_text("RUN")
        # # repeat 100 times to ensure all input is processed
        # for _ in range(100):
        #     #hardware_access.type_text("A")
        #     hardware_access.tap_key("Return")
        #     # Give some time for the program to start
        #     time.sleep(0.5)

        #hardware_access.type_text("2010 REM AEIOU 12345678(!!!) POKE ((Y*40)+X) CHR$(32)")
        #hardware_access.tap_key("Return")

        # hardware_access.type_text("LIST")
        # hardware_access.tap_key("Return")
        # hardware_access.type_text("RUN")
        # hardware_access.tap_key("Return")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if hardware_access:
            hardware_access.close()