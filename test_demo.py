# test_demo.py
# This script simulates what Claude/Cursor would do when calling your tool.

from src.server import analyze_demo_infrastructure

print("... Simulating Agent Run ...\n")

# Call the function directly (bypassing the MCP protocol for testing)
result = analyze_demo_infrastructure()

print(result)