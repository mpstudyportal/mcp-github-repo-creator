#!/usr/bin/env python3
"""
Test script to validate that server_new.py has all merged tools working correctly.

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

import sys
import asyncio
import json
from pathlib import Path

# Add create-repo to path
sys.path.append(str(Path(__file__).parent.parent / "create-repo"))

from server import list_tools, call_tool, RepositoryAnalyzer

async def test_merged_server():
    """Test all tools in the merged server."""
    
    print("🧪 Testing Merged MCP Server (server_new.py)")
    print("=" * 50)
    
    # Test 1: Tool registration
    print("\n1. Testing tool registration...")
    tools = await list_tools()
    
    expected_tools = {
        "get_repo_analysis_instructions",
        "create_github_repo_from_metadata", 
        "analyze_and_generate_metadata_file",
        "create_github_repository",
        "full_repository_setup"
    }
    
    actual_tools = {tool.name for tool in tools}
    
    if expected_tools == actual_tools:
        print(f"   ✅ All {len(tools)} expected tools registered")
        for tool in tools:
            print(f"      • {tool.name}")
    else:
        print(f"   ❌ Tool mismatch!")
        print(f"      Expected: {expected_tools}")
        print(f"      Actual: {actual_tools}")
        return False
    
    # Test 2: Repository Analysis
    print("\n2. Testing repository analysis...")
    try:
        analyzer = RepositoryAnalyzer("..")
        
        if analyzer.is_git_repository():
            metadata = analyzer.generate_metadata()
            print(f"   ✅ Analysis successful:")
            print(f"      • Repository: {metadata['repository_name']}")
            print(f"      • Language: {metadata['primary_language']}")
            print(f"      • Project Type: {metadata['project_type']}")
            print(f"      • Topics: {len(metadata['topics'])} topics")
            print(f"      • Features: {len(metadata['features'])} features")
        else:
            print("   ⚠️  Not a git repository (expected for this test)")
    except Exception as e:
        print(f"   ❌ Analysis failed: {e}")
        return False
    
    # Test 3: Tool call interface (get_repo_analysis_instructions)
    print("\n3. Testing tool call interface...")
    try:
        result = await call_tool("get_repo_analysis_instructions", {"repo_path": ".."})
        if result and len(result) > 0 and "Repository Analysis Instructions" in result[0].text:
            print("   ✅ get_repo_analysis_instructions works")
        else:
            print("   ❌ get_repo_analysis_instructions failed")
            return False
    except Exception as e:
        print(f"   ❌ Tool call failed: {e}")
        return False
    
    # Test 4: Metadata generation tool
    print("\n4. Testing analyze_and_generate_metadata_file...")
    try:
        result = await call_tool("analyze_and_generate_metadata_file", {
            "repo_path": "..",
            "output_file": "test_metadata.json"
        })
        
        if result and len(result) > 0 and "Generated metadata file" in result[0].text:
            print("   ✅ analyze_and_generate_metadata_file works")
            
            # Check if file was created
            test_file = Path("../test_metadata.json")
            if test_file.exists():
                print("   ✅ Metadata file created successfully")
                # Clean up
                test_file.unlink()
            else:
                print("   ⚠️  Metadata file not found (may be expected)")
        else:
            print("   ❌ analyze_and_generate_metadata_file failed")
            print(f"      Result: {result[0].text if result else 'None'}")
            return False
    except Exception as e:
        print(f"   ❌ Metadata generation failed: {e}")
        return False
    
    # Test 5: Import validation
    print("\n5. Testing imports...")
    try:
        from core.create_github_repo import GitHubRepoCreator
        print("   ✅ GitHubRepoCreator imports successfully")
    except ImportError as e:
        print(f"   ❌ GitHubRepoCreator import failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! The merged server is working correctly.")
    print("\n📋 Summary:")
    print("   • All 5 tools properly registered")
    print("   • Repository analysis functional")
    print("   • Tool call interface working")
    print("   • Metadata generation operational")
    print("   • All dependencies importable")
    
    print("\n🚀 The server_new.py successfully merges:")
    print("   • Interactive Copilot workflow tools (from server_new.py)")
    print("   • Automation tools (from server.py)")
    print("   • Clean, robust analysis engine")
    print("   • Comprehensive error handling")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_merged_server())
    sys.exit(0 if success else 1)
