import chainlit as cl

@cl.step(type="tool")
async def tool():
    # Fake tool
    await cl.sleep(2)
    return "Response from the tool!"

@cl.on_message  # this function will be called every time a user inputs a message in the UI
async def main(message: cl.Message):
    """
    This function is called every time a user inputs a message in the UI.
    It sends back an intermediate response from the tool, followed by the final answer.

    Args:
        message: The user's message.

    Returns:
        None.
    """


    # Call the tool
    tool_res = await tool()

    await cl.Message(content=tool_res).send()

# Run Chainlit if this script is executed directly
if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)    