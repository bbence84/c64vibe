

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

import os
import cv2
import time
import base64
import subprocess
import logging
from langchain.tools import tool, ToolRuntime
from typing import Annotated, Literal, NotRequired
from tools.agent_state import VibeC64AgentState
from utils.c64_hw import C64HardwareAccess
import utils.agent_utils as agent_utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestingTools:
    def __init__(self, llm_access):
        self.model_screen_ocr = None
        self.model_coder = None
        self._init_c64_keyboard()
        self.capture_device_connected = True if os.getenv("USB_CAMERA_INDEX") is not None and os.getenv("USB_CAMERA_INDEX").strip() != "" else False
        self.llm_access = llm_access

    def tools(self):

        @tool("CaptureC64Screen", description="Captures the current screen of the C64 and returns what is displayed, related to the provided additional context / question")
        def capture_c64_screen(additional_context: Annotated[str, "What the program should do or what should be checked on the screenshot."] = "") -> str:
            if self.model_screen_ocr is None:
                self.model_screen_ocr = self.llm_access.get_llm_model(create_new=True, streaming=False)
            return self._capture_c64_screen(additional_context)

        @tool("RestartC64", description="Restarts the connected Commodore 64 hardware")
        def restart_c64(runtime: ToolRuntime[None, VibeC64AgentState]) -> str:
            return self._restart_c64()
        
        @tool("SendTextToC64", description="Sends the given text or key press on the connected Commodore 64 hardware keyboard")
        def send_text_to_c64(
            runtime: ToolRuntime[None, VibeC64AgentState],
            text_to_type: Annotated[str, "Text to send to the Commodore 64 keyboard."],
            press_return: Annotated[bool, "Whether to press Return after typing the text."] = False,
            single_key: Annotated[bool, f"""If true, the text_to_type represents a single key to press rather than a string of text. For single keys, you can send "Return", "Space", "0", "1", ..., "9" (without quotes) as text_to_type"""] = False,
            ) -> str:
            return self._send_text_to_c64(text_to_type, press_return)  
        
        @tool("AnalyzeGameMechanics", description="Analyzes the game mechanics based the source code of the game.")
        def analyze_game_mechanics(
            runtime: ToolRuntime[None, VibeC64AgentState],
            ) -> str:
            if self.model_coder is None:
                self.model_coder = self.llm_access.get_llm_model(create_new=True, streaming=False)
            return self._analyze_game_mechanics(runtime)
        
        tools = []
        if self.capture_device_connected:
            tools.append(capture_c64_screen)

        if self.c64keyboard_connected:
            #tools.append(restart_c64)
            tools.append(send_text_to_c64)   
            tools.append(analyze_game_mechanics)         

        return tools
    
    def is_c64keyboard_connected(self):
        return self.c64keyboard_connected    
    
    def is_capture_device_connected(self):
        return self.capture_device_connected    
    
    def _restart_c64(self):
        self.c64keyboard.restart_c64()
        return "Commodore 64 restarted."    
    
    def _init_c64_keyboard(self):
        try:
            keyboard_port = os.getenv("C64_KEYBOARD_DEVICE_PORT")
            if keyboard_port is None or keyboard_port.strip() == "":
                self.c64keyboard_connected = False
                return
            self.c64keyboard = C64HardwareAccess(device_port=keyboard_port, baud_rate=19200, debug=False)
            self.c64keyboard_connected = True
        except Exception as e:
            logger.warning(f"Could not connect to C64 keyboard hardware on port {keyboard_port}. Continuing without keyboard access.")
            self.c64keyboard_connected = False    
    
    def _send_text_to_c64(self, text_to_type: str, press_return: bool = False, single_key: bool = False) -> str:
        if self.is_c64keyboard_connected():
            if single_key:
                self.c64keyboard.tap_key(text_to_type)
                print(f"Sent single key {text_to_type} to C64 keyboard.")
            else:
                self.c64keyboard.type_text(text_to_type)
                print(f"Sent text {text_to_type} to C64 keyboard.")
            if press_return:
                self.c64keyboard.tap_key("Return")
            time.sleep(1)  # Give some time for the C64 to process the input
            return f"Text {text_to_type} sent to C64 keyboard."
        else:
            return "Error: C64 keyboard hardware not connected. Cannot send text."
        
    def _analyze_game_mechanics(self, runtime: ToolRuntime[None, VibeC64AgentState]) -> str:
        source_code = runtime.state.get("current_source_code", "")

        analysis_results = self.model_coder.invoke([
            {"role": "system", "content": "You are an expert Commodore 64 programmer and game designer. You understand the C64 BASIC programming language. You can analyze C64 game source code and explain the game mechanics in detail, for example, how to control the game, what the player can do, and any interesting features or behaviors in the code."},
            {"role": "user",  "content": 
            f"""
            Please analyze the following Commodore 64 game source code and explain the game mechanics in detail. Describe how the game works, what the player can do, and any interesting features or behaviors in the code.

            Here is the source code:
            {source_code}
            """},
        ])
        return agent_utils.get_message_content(analysis_results.content)

    def _capture_c64_screen(self, additional_context: Annotated[str, "What the program should do or what should be checked on the screenshot."] = "") -> str:
        # Capture the screen from the C64 hardware using the webcam
        image_path = get_webcam_snapshot()

        # Encode the image to base64 for sending to the LLM
        b64 = encode_image(image_path)
        img_base64 = f"data:image/png;base64,{b64}"
        img_message = { "type": "image_url", "image_url": { "url": img_base64, },}

        # OCR the image using a multimodal LLM
        ocr_results = self.model_screen_ocr.invoke([
            {"role": "system", "content": "You know understand Commodore 64 screens, how program listings and outputs look like. You know how C64 programs and games look like. You can read text from images of C64 screens accurately."},
            {"role": "user",  "content": 
            [ {"type": "text", "text": 
                f"""
                Please analyze the image carefully and return what you see. If it's a simple text based program, return it as pure text, properly idented and formatted. If it's a graphical screen i.e. a game, describe what you can see and tell if there's anything unusual i.e. error messages and exception, etc."""
                if additional_context == "" else
                f"""
                The additional context that should be anwsered, i.e. what the program does or what should be checked: {additional_context}. Please compare what you see on the screen with this context.
                """
                }, img_message,]},
        ])
        return agent_utils.get_message_content(ocr_results.content)

def get_webcam_snapshot():
    usb_cam_index = os.getenv("USB_CAMERA_INDEX")
    if usb_cam_index is None or usb_cam_index.strip() == "":
        logger.warning("USB_CAMERA_INDEX environment variable is not set. Cannot capture webcam snapshot.")
        return None
    else:
        logger.info(f"Using USB camera index: {usb_cam_index}")

    absolute_path = os.path.join(os.getcwd(), 'output', 'webcam_snapshot.jpg')
    # Delete image if it already exists
    if os.path.exists(absolute_path):
        os.remove(absolute_path)
    
    camera = cv2.VideoCapture(int(usb_cam_index) + cv2.CAP_DSHOW)  

    if not camera.isOpened():
        logger.warning(f"Could not open webcam with index {usb_cam_index}.")
        return None
   
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
    camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Enable autofocus
    camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Enable auto-exposure (0.25 or 1 depending on camera)
    camera.set(cv2.CAP_PROP_AUTO_WB, 1)  # Enable auto white balance

    # Give camera time to initialize after setting properties
    time.sleep(0.5)

    # Warm up the camera with multiple frame captures
    for i in range(5):  # Increased from 15 to 30 frames
        temp_ret, temp_frame = camera.read()
        if not temp_ret:
            logger.warning(f"Failed to read warm-up frame {i+1}")
        time.sleep(0.1)  # 100ms delay between frames for camera adjustment

    time.sleep(0.5)

    # Now take the actual photo
    return_value, image = camera.read()
    
    if return_value:
        cv2.imwrite(absolute_path, image)
        logger.info(f"Webcam snapshot saved to {absolute_path}")
    else:
        logger.warning("Failed to capture image from webcam.")
        absolute_path = None

    camera.release()
    return absolute_path

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()    
    # Send Space key to C64
    # testing_tools = TestingTools(llm_access=None)
    # print(testing_tools._send_text_to_c64("Space", press_return=False, single_key=True))
    # time.sleep(2)
    # print(testing_tools._send_text_to_c64("GO EAST", press_return=True, single_key=False))
    # #print(testing_tools._send_text_to_c64("CTRL+Arrow", press_return=False, single_key=True))

    print(get_webcam_snapshot())
# # #     #convert_c64_bas_to_prg("""C:\output\guessing_game.bas""")
# # #     #hardware_access = C64HardwareAccess(device_port="COM3", baud_rate=19200, debug=False)
# # #     send_prg_to_c64("""C:\output\guessing_game.prg""")    