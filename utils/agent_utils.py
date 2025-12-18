import base64
import os
import cv2
import time
import subprocess

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.c64_hw import C64HardwareAccess

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_webcam_snapshot():
    file_name = ('output/webcam_snapshot.png')
    camera = cv2.VideoCapture(1 + cv2.CAP_DSHOW)  
    #camera = cv2.VideoCapture(0)  
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
    return_value, image = camera.read()
    cv2.imwrite(file_name, image)
    del(camera)
    return file_name

def read_example_programs(num_examples: int = 5) -> str:
    examples = []
    example_files = os.listdir("resources/examples")
    for i, filename in enumerate(example_files):
        if i >= num_examples:
            break
        with open(os.path.join("resources/examples", filename), "r") as f:
            examples.append(f.read())
    return "\n\n".join(examples)

def convert_c64_bas_to_prg(bas_file_path: str) -> str:
    # Execute the bas2prg.exe in the utilities folder to convert .bas to .prg
    bas2prg_exe_path = os.path.join("utilities", "bas2prg.exe")
    # How to call: bas2prg.exe -o guess_hun.prg guess_hun.bas
    prg_file_path = bas_file_path.replace(".bas", ".prg")
    subprocess.run([bas2prg_exe_path, "-o", prg_file_path, bas_file_path], check=True)
    return prg_file_path


# if __name__ == "__main__":
#     #print(get_webcam_snapshot())
#     #convert_c64_bas_to_prg("""C:\output\guessing_game.bas""")
#     #hardware_access = C64HardwareAccess(device_port="COM3", baud_rate=19200, debug=False)
#     send_prg_to_c64("""C:\output\guessing_game.prg""")