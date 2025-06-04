"""
AgentExecutive Runner Script

Start script voor de AgentExecutive applicatie.
"""

import logging
import tkinter as tk
import asyncio
from pathlib import Path

from src.ui.app import AgentExecutiveApp  # Correct import for AgentExecutiveApp
from src.handlers.web_handler import WebPageHandler  # Correct import for WebPageHandler

async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize the WebPageHandler asynchronously (Playwright)
    web_handler = WebPageHandler()
    await web_handler.start_browser()  # Make sure the browser is started

    # Create the main Tkinter root window
    root = tk.Tk()

    # Create an instance of AgentExecutiveApp, passing in the root window and web handler
    app = AgentExecutiveApp(root, web_handler)

    # Start the Tkinter main event loop (this will run in the main thread)
    root.mainloop()

    # Cleanup Playwright after GUI closes
    await web_handler.cleanup()  # Properly await cleanup in the async function

if __name__ == "__main__":
    # Run the main function using asyncio
    asyncio.run(main())