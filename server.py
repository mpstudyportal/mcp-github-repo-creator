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
from core.create_github_repo import GitHubRepoCreator

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

        # Use the enhanced GitHubRepoCreator class
        creator = GitHubRepoCreator(
            metadata_file=str(metadata_file) if save_metadata_file else None,
            project_dir=str(repo_path_obj)
        )

        # If we didn't save the metadata file, set it directly
        if not save_metadata_file:
            creator.metadata = metadata
            creator.repo_name = metadata.get("repository_name", "")

        # Check prerequisites
        success, issues = creator.check_prerequisites()
        if issues:
            warnings = "\n".join([f"   {issue}" for issue in issues])
            return f"⚠️  Prerequisites check found issues:\n{warnings}\n\nProceeding anyway..."

        # Check GitHub CLI authentication
        if not creator.check_github_cli_auth():
            return "❌ GitHub CLI not available or not authenticated. Please run: gh auth login"

        # Create the repository using the enhanced method
        if creator.create_repository():
            topics = metadata.get('topics', [])
            return get_repository_creation_success_message(
                repo_name=metadata['repository_name'],
                description=metadata['description'],
                topics=topics,
                metadata=metadata
            )
        else:
            return "❌ Failed to create GitHub repository. Check the output above for details."

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
        
        # Use the enhanced GitHubRepoCreator class
        creator = GitHubRepoCreator(
            metadata_file=metadata_file,
            project_dir=str(repo_path_obj)
        )

        # Validate metadata
        metadata_valid, metadata_issues = creator.validate_metadata()
        if not metadata_valid:
            issues_text = "\n".join([f"   {issue}" for issue in metadata_issues])
            return f"❌ Metadata validation failed:\n{issues_text}"

        # Check prerequisites  
        success, issues = creator.check_prerequisites()
        if issues:
            warnings = "\n".join([f"   {issue}" for issue in issues])
            return f"⚠️  Prerequisites check found issues:\n{warnings}\n\nProceeding anyway..."

        # Check GitHub CLI authentication
        if not creator.check_github_cli_auth():
            return "❌ GitHub CLI not available or not authenticated. Please run: gh auth login"

        # Create the repository using the enhanced method
        if creator.create_repository():
            metadata = creator.metadata
            topics = metadata.get('topics', [])
            return get_repository_creation_success_message(
                repo_name=metadata['repository_name'],
                description=metadata['description'],
                topics=topics,
                metadata=metadata
            )
        else:
            return "❌ Failed to create GitHub repository. Check the output above for details."

    except Exception as e:
        return f"❌ Error creating GitHub repository: {str(e)}"


@app.tool()
def manage_repository_topics(repo_path: str = ".", metadata_file: str = "github_repo_metadata.json") -> str:
    """
    Manage topics for an existing GitHub repository using metadata file.
    
    Args:
        repo_path: Path to the repository
        metadata_file: Path to the metadata JSON file
    
    Returns:
        Result message indicating success or failure
    """
    try:
        # Use the enhanced GitHubRepoCreator class for topic management
        creator = GitHubRepoCreator(
            metadata_file=metadata_file,
            project_dir=repo_path
        )

        # Validate metadata
        metadata_valid, metadata_issues = creator.validate_metadata()
        if not metadata_valid:
            issues_text = "\n".join([f"   {issue}" for issue in metadata_issues])
            return f"❌ Metadata validation failed:\n{issues_text}"

        # Check GitHub CLI authentication
        if not creator.check_github_cli_auth():
            return "❌ GitHub CLI not available or not authenticated. Please run: gh auth login"

        # Use the enhanced topic management
        if creator.manage_existing_repository_topics():
            return "✅ Repository topics updated successfully!"
        else:
            return "❌ Failed to update repository topics. Check the output above for details."

    except Exception as e:
        return f"❌ Error managing repository topics: {str(e)}"


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
        # Step 1: Analyze repository and generate metadata
        analyzer = RepositoryAnalyzer(repo_path)

        if not analyzer.is_git_repository():
            return "❌ Error: Not a git repository. Please run this from within a git repository."

        # Generate metadata
        metadata = analyzer.generate_metadata()

        # Override repository name if provided
        if repository_name:
            metadata["repository_name"] = repository_name

        # Step 2: Save metadata file
        repo_path_obj = Path(repo_path).resolve()
        metadata_path = repo_path_obj / "github_repo_metadata.json"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Step 3: Create GitHub repository using enhanced GitHubRepoCreator
        creator = GitHubRepoCreator(
            metadata_file=str(metadata_path),
            project_dir=str(repo_path_obj)
        )

        # Check prerequisites
        success, issues = creator.check_prerequisites()
        if issues:
            warnings = "\n".join([f"   {issue}" for issue in issues])
            return f"⚠️  Prerequisites check found issues:\n{warnings}\n\nCannot proceed with full setup."

        # Check GitHub CLI authentication
        if not creator.check_github_cli_auth():
            return "❌ GitHub CLI not available or not authenticated. Please run: gh auth login"

        # Create the repository
        if creator.create_repository():
            return get_full_setup_success_message(metadata)
        else:
            return f"❌ Repository analysis and metadata generation succeeded, but GitHub repository creation failed."

    except Exception as e:
        return f"❌ Error in full repository setup: {str(e)}"


def main():
    """Run the MCP server."""
    app.run()


if __name__ == "__main__":
    main()
