#!/usr/bin/env python3
"""
Templates module for GitHub repository creation MCP server.

This module contains all the long string templates used by the MCP server,
providing centralized template management and better maintainability.

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

import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


def get_repository_analysis_instructions(repo_path_obj: Path, example_metadata: Dict[str, Any]) -> str:
    """
    Generate detailed instructions for Copilot on how to analyze the repository and create metadata JSON.

    Args:
        repo_path_obj: Path object to the repository
        example_metadata: Example metadata structure to show in instructions

    Returns:
        Detailed instructions for repository analysis and metadata creation
    """
    instructions = f"""
# 🚀 Repository Analysis Instructions for GitHub Repository Creation

## Overview
I need you to analyze this repository and create a `github_repo_metadata.json` file that will be used to automatically create a GitHub repository and connect it to this local repository.

## Step 1: Analyze the Repository
Please examine the current repository and gather the following information:

### 🔍 Required Analysis:
1. **Repository Name**: Based on directory name or existing git remote
2. **Description**: Look for:
   - README.md content (first meaningful paragraph)
   - Package.json description
   - setup.py description
   - Docstrings in main files
3. **Primary Language**: Detect from file extensions and counts
4. **Project Type**: Classify based on files/structure:
   - "Web Application" (React, Next.js, etc.)
   - "API/Backend" (FastAPI, Express, etc.)
   - "CLI Tool" (command-line applications)
   - "Library/Package" (npm/pip packages)
   - "AI/ML" (machine learning projects)
   - "Mobile App" (React Native, Flutter)
   - "Desktop App" (Electron, Tauri)
   - "Game" (Unity, Godot)
   - "Documentation" (docs sites)
   - "Other"
5. **License**: Check for LICENSE file or package.json
6. **Topics/Tags**: Generate relevant topics based on:
   - Technologies used (react, python, typescript, etc.)
   - Frameworks (nextjs, fastapi, flask, etc.)
   - Categories (web-app, cli, ai, etc.)
   - Domains (finance, healthcare, etc.)
7. **Features**: List main features from README or code analysis

## Step 2: Create Metadata JSON
Create a JSON object with this **exact structure**:

```json
{json.dumps(example_metadata, indent=2)}
```

## Step 3: Analysis Guidelines

### 📁 Files to Examine:
- `README.md` (primary source for description and features)
- `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` (metadata)
- `requirements.txt`, `Pipfile`, `yarn.lock` (dependencies)
- Main source files (detect patterns and frameworks)
- `LICENSE` or `LICENSE.txt`
- Directory structure

### 🏷️ Topic Generation Rules:
- Include primary language (python, javascript, typescript, etc.)
- Include frameworks/libraries (react, nextjs, fastapi, flask, etc.)
- Include categories (web-app, cli-tool, api, machine-learning, etc.)
- Include domains if applicable (finance, healthcare, education, etc.)
- Keep topics lowercase, use hyphens for multi-word topics
- Limit to 10-20 most relevant topics

### 📝 Description Guidelines:
- Start with an emoji that represents the project
- Keep it concise but descriptive (1-3 sentences)
- Mention key technologies and benefits
- Avoid technical jargon unless necessary

## Step 4: Submit the Result
After your analysis, provide me with:
1. A brief summary of what you found
2. The complete JSON metadata object
3. Any questions or uncertainties

Once you provide the JSON metadata, I'll use it to automatically:
- Create the GitHub repository
- Configure topics and settings  
- Connect the local repository to GitHub
- Push the code to the remote repository

## Current Repository Path: `{repo_path_obj}`

Please proceed with the analysis and provide the metadata JSON! 🎯
        """
    return instructions.strip()


def get_repository_creation_success_message(
    repo_name: str,
    description: str,
    topics: List[str],
    metadata: Dict[str, Any]
) -> str:
    """
    Generate a success message for GitHub repository creation.

    Args:
        repo_name: Name of the created repository
        description: Repository description
        topics: List of repository topics
        metadata: Full metadata dictionary

    Returns:
        Formatted success message
    """
    success_message = f"""
🎉 GitHub Repository Created Successfully!

📋 Repository Details:
   Name: {repo_name}
   Description: {description[:100]}...
   Topics: {len(topics)} topics added
   Type: {metadata.get('project_type', 'N/A')}
   Language: {metadata.get('primary_language', 'N/A')}

✅ Completed Actions:
   • Created private GitHub repository
   • Added remote origin to local repository  
   • Pushed code to GitHub
   • Added repository topics
   • Configured repository settings (issues, wiki, projects)

🌐 Your repository is now available on GitHub!
   Run: gh repo view {repo_name} --web

📄 Metadata saved to: github_repo_metadata.json
            """
    return success_message.strip()


def get_full_setup_success_message(metadata: Dict[str, Any]) -> str:
    """
    Generate a success message for complete repository setup.

    Args:
        metadata: Repository metadata dictionary

    Returns:
        Formatted complete setup success message
    """
    complete_result = "🎉 Complete Repository Setup Successful!\n"
    complete_result += "=" * 50 + "\n"
    complete_result += f"✅ Repository analyzed and metadata generated\n"
    complete_result += f"✅ Metadata saved: github_repo_metadata.json\n"
    complete_result += f"✅ GitHub repository created: {metadata['repository_name']}\n"
    complete_result += f"✅ Local repository connected to GitHub\n"
    complete_result += f"✅ Code pushed to remote repository\n"
    complete_result += f"✅ Topics and settings configured\n\n"
    complete_result += f"📊 Repository Details:\n"
    complete_result += f"   🌐 Name: {metadata['repository_name']}\n"
    complete_result += f"   📝 Description: {metadata['description'][:100]}...\n"
    complete_result += f"   🏷️  Topics: {len(metadata['topics'])} topics\n"
    complete_result += f"   💻 Language: {metadata['primary_language']}\n"
    complete_result += f"   📄 Type: {metadata['project_type']}\n"
    complete_result += f"   📜 License: {metadata.get('license', 'N/A')}\n\n"
    complete_result += "🚀 Your repository is now live on GitHub!"
    complete_result += f"\n🔍 View it: gh repo view {metadata['repository_name']} --web"

    return complete_result


def get_example_metadata_structure() -> Dict[str, Any]:
    """
    Get the example metadata structure to show in instructions.

    Returns:
        Example metadata dictionary
    """
    return {
        "repository_name": "example-project",
        "description": "🚀 MCP GitHub Repository Creator - A Model Context Protocol server that provides tools for AI applications like GitHub Copilot to automatically analyze repositories and create GitHub repositories. Features repository analysis, topic management, automated setup, and seamless integration with MCP-compatible AI clients.",
        "topics": ["mcp",
                   "model-context-protocol",
                   "github",
                   "repository-automation",
                   "copilot",
                   "python",
                   "ai-tools",
                   "automation",
                   "fastmcp",
                   "cli-tool",
                   "github-cli",
                   "repository-analysis",
                   "metadata-generation",
                   "mcp-server",
                   "developer-tools",
                   "workflow-automation",
                   "git",
                   "github-api",
                   "ai-integration"],
        "created_date": datetime.now().strftime('%Y-%m-%d'),
        "project_type": "MCP Server/CLI Tool",
        "primary_language": "Python",
        "license": "GPL-3.0",
        "features": ["Repository analysis and metadata extraction",
                     "GitHub repository creation with proper configuration",
                     "MCP-compatible tool interface for AI applications",
                     "Automated topic management based on project analysis",
                     "Complete workflow from analysis to repository setup",
                     "GitHub CLI integration for secure authentication",
                     "Support for multiple AI clients (Copilot, Claude, etc.)",
                     "Centralized template management",
                     "Private repository creation by default",
                     "Comprehensive error handling and troubleshooting"]
    }
