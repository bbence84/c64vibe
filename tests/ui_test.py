
import chainlit as cl
import base64
import os

@cl.on_chat_start
async def main():       

        with open("output/BEJGLI_20251225201027.prg", "rb") as f:
                prg_data = f.read()
        prg_base64 = base64.b64encode(prg_data).decode()
    

        props = {
                "button_label": "🎮 Launch Game in Online C64 Emulator",
                "target_origin": "http://ty64.krissz.hu",
                "prg_binary_base64": prg_base64,}

        emulator_link = cl.CustomElement(name="EmulatorLink", props=props)

        temp_bas_path = os.path.join("output", f"adventure_final.bas")
        with open(temp_bas_path, "r") as f:
                bas_code = f.read()

        file_element = cl.File(name="test.prg", content=prg_data, description="Generated C64 BASIC V2.0 prg file.")

        msg = await cl.Message(content="test message", elements=[emulator_link, file_element]).send()

        async with cl.Step(type="tool", name="Step") as parent_step:
                parent_step.input = "Parent step input"

                markdown_example = """Here is an example of **Markdown** *formatting*:
                        - Item 1
                        - Item 2
                        > This is a blockquote.""" 

                parent_step.input = markdown_example
                parent_step.output = markdown_example

                parent_step.default_open = True
                parent_step.show_input = True

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)
