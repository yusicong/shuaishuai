
import sys
import os
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.current_time import CurrentTimeTool, CurrentTimeInput

def test_tool_args():
    tool = CurrentTimeTool()
    print(f"Tool args schema: {tool.args_schema.schema()}")
    
    # Test with empty args - Should pass
    try:
        print("Testing with empty args...")
        tool.run({}) 
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")

    # Test with extra args - Might fail if not handled
    try:
        print("Testing with extra args {'query': 'now'}...")
        tool.run({"query": "now"})
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    test_tool_args()
