"""
AgentExecutive Runner Script

Start script voor de AgentExecutive applicatie.
"""

import os
import sys
from pathlib import Path

def main():
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    
    # Add to Python path
    sys.path.insert(0, str(project_root))
    
    # Now import and run the application
    from src.main import main as app_main
    return app_main()

if __name__ == "__main__":
    sys.exit(main())