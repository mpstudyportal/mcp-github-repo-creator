#!/usr/bin/env python3
"""
Test the MCP GitHub Repository Creator

This script demonstrates the interactive workflow:
1. Get instructions for analyzing the repository
2. Simulate Copilot creating metadata JSON  
3. Create the GitHub repository from metadata

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

from server import RepositoryAnalyzer, call_tool, TextContent
import asyncio
import json
import sys
from pathlib import Path

# Add the server path
sys.path.append(str(Path(__file__).parent))


async def test_workflow():
    """Test the complete MCP workflow."""

    print("🚀 Testing MCP GitHub Repository Creator Workflow")
    print("=" * 60)

    # Step 1: Get instructions for repository analysis
    print("\n📋 Step 1: Getting analysis instructions...")

    instructions_result = await call_tool(
        "get_repo_analysis_instructions",
        {"repo_path": "/mnt/[WDG]auxiliary/Desktop/VScode_projects-AI/github-repo-tools"}
    )

    print("✅ Instructions generated:")
    print(instructions_result[0].text[:500] + "...\n")

    # Step 2: Simulate Copilot analyzing the repository and creating metadata
    print("📊 Step 2: Analyzing repository (simulating Copilot's work)...")

    analyzer = RepositoryAnalyzer(
        "/mnt/[WDG]auxiliary/Desktop/VScode_projects-AI/github-repo-tools")

    if analyzer.is_git_repository():
        print("✅ Git repository detected")

        # Generate metadata automatically (this simulates what Copilot would do)
        metadata = analyzer.generate_metadata()

        print(f"✅ Generated metadata:")
        print(f"   Repository: {metadata['repository_name']}")
        print(f"   Language: {metadata['primary_language']}")
        print(f"   Type: {metadata['project_type']}")
        print(f"   Topics: {len(metadata['topics'])} topics")
        print(f"   Description: {metadata['description'][:100]}...")

        # Convert metadata to JSON string (this is what Copilot would provide)
        metadata_json = json.dumps(metadata, indent=2)

        print(f"\n📄 Metadata JSON (first 300 chars):")
        print(metadata_json[:300] + "...\n")

        # Step 3: Create GitHub repository from metadata
        print("🚀 Step 3: Creating GitHub repository from metadata...")

        creation_result = await call_tool(
            "create_github_repo_from_metadata",
            {
                "metadata_json": metadata_json,
                "repo_path": "/mnt/[WDG]auxiliary/Desktop/VScode_projects-AI/github-repo-tools",
                "save_metadata_file": True
            }
        )

        print("📤 Repository creation result:")
        print(creation_result[0].text)

    else:
        print("❌ Not a git repository")

    print("\n🎉 MCP Workflow Test Complete!")


async def test_instructions_only():
    """Test just the instructions generation."""

    print("🔍 Testing Instructions Generation Only")
    print("=" * 50)

    # Test with current directory
    instructions_result = await call_tool(
        "get_repo_analysis_instructions",
        {"repo_path": "."}
    )

    print("📋 Generated Instructions:")
    print(instructions_result[0].text)


if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Full workflow test (analyze + create repo)")
    print("2. Instructions only test")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(test_workflow())
    else:
        asyncio.run(test_instructions_only())
