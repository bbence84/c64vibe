from langchain.tools import tool, ToolRuntime
from typing import Annotated, Literal, NotRequired
import utils.agent_utils as agent_utils

class TestingTools:
    def __init__(self, llm_access, capture_device_connected=False):
        self.model_screen_ocr = llm_access.get_llm_model(create_new=True, streaming=False)
        self.capture_device_connected = capture_device_connected

    def tools(self):

        @tool("CaptureC64Screen", description="Captures the current screen of the C64 and returns what is displayed")
        def capture_c64_screen(program_specifications: Annotated[str, "What the program should do in theory."] = "") -> str:
            return self._capture_c64_screen(program_specifications)

        tools = []
        if self.capture_device_connected:
            tools.append(capture_c64_screen)

        return tools

    def _capture_c64_screen(self, program_specifications: Annotated[str, "What the program should do in theory."] = "") -> str:
        # Capture the screen from the C64 hardware using the webcam
        image_path = agent_utils.get_webcam_snapshot()

        # Encode the image to base64 for sending to the LLM
        b64 = agent_utils.encode_image(image_path)
        img_base64 = f"data:image/png;base64,{b64}"
        img_message = { "type": "image_url", "image_url": { "url": img_base64, },}

        # OCR the image using a multimodal LLM
        ocr_results = self.model_screen_ocr.invoke([
            {"role": "system", "content": "You know understand Commodore 64 screens, how program listings and outputs look like. You know how C64 programs and games look like. You can read text from images of C64 screens accurately."},
            {"role": "user",  "content": 
            [ {"type": "text", "text": 
                f"""
                Please analyze the image carefully and return what you see. If it's a simple text based program, return it as pure text, properly idented and formatted. If it's a graphical screen i.e. a game, describe what you can see and tell if there's anything unusual i.e. error messages and exception, etc."""
                if program_specifications == "" else
                f"""
                The program was supposed to do the following: {program_specifications}. Please also compare what you see on the screen with what the program was supposed to do.
                """
                }, img_message,]},
        ])
        return agent_utils.get_message_content(ocr_results.content)

