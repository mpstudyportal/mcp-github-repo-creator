#!/usr/bin/env python3
"""
Demo script showing how to use the MCP GitHub Repository Creator Server

This script demonstrates how to connect to and use the MCP server tools.

Copyright (C) 2025 flickleafy
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def demo_mcp_server():
    """Demonstrate the MCP server functionality."""
    
    # Configure the server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env={}
    )
    
    print("🚀 Starting MCP GitHub Repository Creator Demo")
    print("=" * 50)
    
    try:
        # Connect to the MCP server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                print("✅ Connected to MCP server")
                
                # List available tools
                tools = await session.list_tools()
                print(f"\n📋 Available Tools ({len(tools.tools)}):")
                for tool in tools.tools:
                    print(f"  • {tool.name}: {tool.description}")
                
                # Example: Get repository analysis instructions
                print("\n🔍 Getting repository analysis instructions...")
                result = await session.call_tool(
                    "get_repo_analysis_instructions", 
                    arguments={"repo_path": "."}
                )
                
                if result.content:
                    print("✅ Instructions retrieved successfully!")
                    print("📄 First 200 characters of instructions:")
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        print(f"   {content.text[:200]}...")
                    else:
                        print(f"   {str(content)[:200]}...")
                
                # Example: Analyze and generate metadata
                print("\n🔬 Analyzing repository and generating metadata...")
                result = await session.call_tool(
                    "analyze_and_generate_metadata_file",
                    arguments={"repo_path": ".", "output_file": "demo_metadata.json"}
                )
                
                if result.content:
                    print("✅ Analysis completed!")
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        print("📊 Analysis results:")
                        print(f"   {content.text[:300]}...")
                
                print("\n🎉 Demo completed successfully!")
                print("\n💡 To use the server with Copilot:")
                print("   1. Start the server: python server.py")
                print("   2. Configure your MCP client to connect via stdio")
                print("   3. Use the available tools for GitHub repository creation")
                
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Make sure you're in a git repository and have the virtual environment activated")


def main():
    """Run the demo."""
    asyncio.run(demo_mcp_server())


if __name__ == "__main__":
    main()
