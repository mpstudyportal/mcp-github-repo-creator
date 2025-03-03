#!/usr/bin/env python3
"""
MCP Server for GitHub Repository Creation

This MCP server provides tools for Copilot to:
1. Analyze repository and generate metadata
2. Create GitHub repository from metadata
3. Complete the entire flow of connecting local and remote repositories

The server uses the official MCP SDK to provide standardized tools for AI applications.

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
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os
import re
from datetime import datetime

# Import the official MCP SDK
from mcp.server.fastmcp import FastMCP

# Import the repository analyzer and templates from core module
from core.repository_analyzer import RepositoryAnalyzer
from core.templates import (
    get_repository_analysis_instructions,
    get_repository_creation_success_message,
    get_full_setup_success_message,
    get_example_metadata_structure
)

# Initialize the FastMCP server
app = FastMCP("github-repo-creator")


@app.tool()
def get_repo_analysis_instructions(repo_path: str = ".") -> str:
    """
    Get detailed instructions for Copilot on how to analyze the repository and create metadata JSON.
    
    Args:
        repo_path: Path to the repository (default: current directory)
    
    Returns:
        Detailed instructions for repository analysis and metadata creation
    """
    try:
        # Basic repository validation
        repo_path_obj = Path(repo_path).resolve()
        if not (repo_path_obj / ".git").exists():
            return "❌ Error: Not a git repository. Please run this from within a git repository."

        # Get example metadata structure
        example_metadata = get_example_metadata_structure()

        # Generate instructions using the template function
        return get_repository_analysis_instructions(repo_path_obj, example_metadata)

    except Exception as e:
        return f"❌ Error generating instructions: {str(e)}"


@app.tool()
def create_github_repo_from_metadata(
    metadata_json: str,
    repo_path: str = ".",
    save_metadata_file: bool = True
) -> str:
    """
    Receive the generated metadata JSON and create the GitHub repository with full setup.
    
    Args:
        metadata_json: The complete metadata JSON content as a string
        repo_path: Path to the local repository
        save_metadata_file: Whether to save the metadata to github_repo_metadata.json
    
    Returns:
        Result message indicating success or failure
    """
    try:
        # Parse the metadata JSON
        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError as e:
            return f"❌ Error: Invalid JSON metadata: {str(e)}"

        # Validate required fields
        required_fields = ["repository_name", "description"]
        missing_fields = [field for field in required_fields if not metadata.get(field)]
        if missing_fields:
            return f"❌ Error: Missing required fields in metadata: {', '.join(missing_fields)}"

        repo_path_obj = Path(repo_path).resolve()

        # Save metadata file if requested
        if save_metadata_file:
            metadata_file = repo_path_obj / "github_repo_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Check GitHub CLI authentication
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return "❌ GitHub CLI not available or not authenticated. Please run: gh auth login"
        except FileNotFoundError:
            return "❌ GitHub CLI not installed. Please install it from: https://cli.github.com/"

        # Change to the repository directory
        original_cwd = os.getcwd()
        os.chdir(repo_path_obj)

        try:
            # Step 1: Create the repository
            repo_name = metadata['repository_name']
            description = metadata['description']
            escaped_description = description.replace('"', '\\"')
            
            result = subprocess.run([
                "gh", "repo", "create", repo_name,
                "--private",
                "--description", escaped_description
            ], capture_output=True, text=True)

            if result.returncode != 0:
                return f"❌ Failed to create repository: {result.stderr}"

            # Step 2: Add remote origin
            result = subprocess.run([
                "git", "remote", "add", "origin",
                f"https://github.com/$(gh api user --jq .login)/{repo_name}.git"
            ], capture_output=True, text=True, shell=True)

            # Step 3: Set main as default branch
            subprocess.run(["git", "branch", "-M", "main"], capture_output=True, text=True)

            # Step 4: Push to GitHub
            result = subprocess.run([
                "git", "push", "-u", "origin", "main"
            ], capture_output=True, text=True)

            if result.returncode != 0:
                return f"❌ Failed to push to GitHub: {result.stderr}"

            # Step 5: Add topics
            topics = metadata.get('topics', [])
            if topics:
                valid_topics = [t.lower().strip() for t in topics if t and len(t.strip()) > 1]
                if valid_topics:
                    topics_string = ",".join(valid_topics[:20])  # GitHub limit
                    subprocess.run([
                        "gh", "repo", "edit", "--add-topic", topics_string
                    ], capture_output=True, text=True)

            # Step 6: Set repository settings
            subprocess.run([
                "gh", "repo", "edit", repo_name,
                "--enable-issues",
                "--enable-wiki",
                "--enable-projects"
            ], capture_output=True, text=True)

            # Get success message using template function
            topics = metadata.get('topics', [])
            return get_repository_creation_success_message(
                repo_name=repo_name,
                description=description,
                topics=topics,
                metadata=metadata
            )

        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    except Exception as e:
        return f"❌ Error creating GitHub repository: {str(e)}"


@app.tool()
def analyze_and_generate_metadata_file(repo_path: str = ".", output_file: str = "github_repo_metadata.json") -> str:
    """
    Analyze the current repository and generate metadata github_repo_metadata.json file.
    
    Args:
        repo_path: Path to the repository
        output_file: Output metadata file path
    
    Returns:
        Analysis results and generated metadata
    """
    try:
        analyzer = RepositoryAnalyzer(repo_path)

        if not analyzer.is_git_repository():
            return "❌ Error: Not a git repository. Please run this from within a git repository."

        # Generate metadata
        metadata = analyzer.generate_metadata()

        # Write metadata to file
        metadata_path = Path(repo_path) / output_file
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        result = f"✅ Generated metadata file: {metadata_path}\n\n"
        result += "📄 Generated metadata:\n"
        result += json.dumps(metadata, indent=2, ensure_ascii=False)
        result += f"\n\n📋 Analysis Summary:"
        result += f"\n   Repository: {metadata['repository_name']}"
        result += f"\n   Language: {metadata['primary_language']}"
        result += f"\n   Type: {metadata['project_type']}"
        result += f"\n   Topics: {len(metadata['topics'])} topics"
        result += f"\n   Features: {len(metadata['features'])} features"

        return result

    except Exception as e:
        return f"❌ Error generating metadata file: {str(e)}"


@app.tool()
def create_github_repository(metadata_file: str = "github_repo_metadata.json", repo_path: str = ".") -> str:
    """
    Create GitHub repository using the metadata file and connect local repo.
    
    Args:
        metadata_file: Path to the metadata JSON file
        repo_path: Path to the local repository
    
    Returns:
        Result message indicating success or failure
    """
    try:
        repo_path_obj = Path(repo_path).resolve()
        metadata_file_path = repo_path_obj / metadata_file

        if not metadata_file_path.exists():
            return f"❌ Error: Metadata file not found: {metadata_file_path}"

        # Load metadata
        with open(metadata_file_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Use the create_github_repo_from_metadata function
        return create_github_repo_from_metadata(
            metadata_json=json.dumps(metadata),
            repo_path=repo_path,
            save_metadata_file=False  # File already exists
        )

    except Exception as e:
        return f"❌ Error creating GitHub repository: {str(e)}"


@app.tool()
def full_repository_setup(repo_path: str = ".", repository_name: str = None) -> str:
    """
    Complete workflow: analyze repo, generate metadata, create GitHub repo, and connect.
    
    Args:
        repo_path: Path to the repository
        repository_name: Override repository name (optional)
    
    Returns:
        Complete setup result message
    """
    try:
        # Step 1: Analyze repository
        analyzer = RepositoryAnalyzer(repo_path)

        if not analyzer.is_git_repository():
            return "❌ Error: Not a git repository. Please run this from within a git repository."

        # Step 2: Generate metadata
        metadata = analyzer.generate_metadata()

        # Override repository name if provided
        if repository_name:
            metadata["repository_name"] = repository_name

        # Step 3: Save metadata file
        repo_path_obj = Path(repo_path).resolve()
        metadata_path = repo_path_obj / "github_repo_metadata.json"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Step 4: Create GitHub repository
        result = create_github_repo_from_metadata(
            metadata_json=json.dumps(metadata),
            repo_path=repo_path,
            save_metadata_file=False  # Already saved
        )

        if "🎉" in result:  # Success indicator
            return get_full_setup_success_message(metadata)
        else:
            return f"❌ Repository analysis succeeded, but GitHub repository creation failed:\n{result}"

    except Exception as e:
        return f"❌ Error in full repository setup: {str(e)}"


def main():
    """Run the MCP server."""
    app.run()


if __name__ == "__main__":
    main()
