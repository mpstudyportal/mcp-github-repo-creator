#!/usr/bin/env python3
"""
GitHub Repository Creation Helper Script

This script generates the necessary commands and information to create a private
GitHub repository based on metadata configuration from a JSON file.

The script is now completely data-driven:
- Repository information is read from github_repo_metadata.json (or custom file)
- Topics are managed by the add_github_topics.py integration
- Create new projects by simply updating the metadata file

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

Author: flickleafy
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set


class GitHubRepoCreator:
    """
    Helper class to create GitHub repositories with automated setup.

    Reads repository information from a JSON metadata file and creates
    the repository with proper configuration including topics. Integrates
    topics management functionality directly without external dependencies.
    """

    def __init__(self, metadata_file: str = None, project_dir: str = None):
        """
        Initialize the GitHub repository creator.

        Args:
            metadata_file: Path to the metadata JSON file
            project_dir: Path to the project directory (default: current working directory)
        """
        self.project_dir = Path(project_dir).resolve() if project_dir else Path.cwd()
        self.current_dir = self.project_dir  # For backward compatibility
        
        if metadata_file:
            # If metadata_file is absolute, use as-is; otherwise, resolve relative to project_dir
            metadata_path = Path(metadata_file)
            if metadata_path.is_absolute():
                self.metadata_file = metadata_path
            else:
                self.metadata_file = self.project_dir / metadata_path
        else:
            self.metadata_file = self.project_dir / "github_repo_metadata.json"
            
        self.metadata = self._load_metadata()
        self.repo_name = self.metadata.get("repository_name", "")
        self.readme_path = self.project_dir / "README.md"

    def _load_metadata(self) -> Dict[str, Any]:
        """
        Load repository metadata from JSON file.

        Returns:
            Dict[str, Any]: Repository metadata

        Time Complexity: O(1)
        """
        try:
            if not self.metadata_file.exists():
                print(
                    f"❌ Error: Metadata file not found: {self.metadata_file}")
                print(
                    "💡 Create a github_repo_metadata.json file with repository information")
                return {}

            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Validate required fields
            required_fields = ["repository_name", "description"]
            missing_fields = [
                field for field in required_fields if not metadata.get(field)]

            if missing_fields:
                print(
                    f"❌ Error: Missing required fields in metadata: {', '.join(missing_fields)}")
                return {}

            return metadata

        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in metadata file: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error loading metadata: {e}")
            return {}

    def generate_repo_description(self) -> str:
        """
        Get repository description from metadata.

        Returns:
            str: Repository description for GitHub

        Time Complexity: O(1)
        """
        return self.metadata.get("description", "No description available")

    def generate_repo_topics(self) -> List[str]:
        """
        Get repository topics from metadata.

        Returns:
            List[str]: List of repository topics

        Time Complexity: O(1)
        """
        return self.metadata.get("topics", [])

    def generate_github_cli_commands(self) -> List[str]:
        """
        Generate GitHub CLI commands to create and setup the repository.

        Returns:
            List[str]: List of commands to execute

        Time Complexity: O(1)
        """
        description = self.generate_repo_description()

        # Escape description for command line
        escaped_description = description.replace('"', '\\"')

        commands = [
            "# Step 1: Create private GitHub repository",
            f'gh repo create {self.repo_name} --private --description "{escaped_description}"',
            "",
            "# Step 2: Add remote origin to local repository",
            f"# First get your GitHub username and add remote",
            f"GITHUB_USER=$(gh api user --jq .login)",
            f"git remote add origin https://github.com/$GITHUB_USER/{self.repo_name}.git",
            "",
            "# Step 3: Set main as default branch",
            "git branch -M main",
            "",
            "# Step 4: Push to GitHub",
            "git push -u origin main",
            "",
            "# Step 5: Set repository settings (optional)",
            f"# Get the full repository path for settings",
            f"REPO_OWNER=$(gh api user --jq .login)",
            f'gh repo edit $REPO_OWNER/{self.repo_name} --enable-issues --enable-wiki --enable-projects',
            "",
            "# Step 6: View the created repository",
            f"gh repo view {self.repo_name} --web"
        ]

        return commands

    def generate_manual_setup_instructions(self) -> List[str]:
        """
        Generate manual setup instructions if GitHub CLI is not available.

        Returns:
            List[str]: Manual setup instructions

        Time Complexity: O(1)
        """
        description = self.generate_repo_description()
        topics = self.generate_repo_topics()

        instructions = [
            "# Manual GitHub Repository Setup Instructions",
            "",
            "## 1. Create Repository on GitHub Web Interface",
            "",
            "1. Go to https://github.com/new",
            f"2. Repository name: {self.repo_name}",
            "3. Description:",
            f'   "{description}"',
            "",
            "4. Select 'Private' repository",
            "5. Do NOT initialize with README (we already have one)",
            "6. Click 'Create repository'",
            "",
            "## 2. Add Topics",
            "",
            "In the repository settings, add these topics:",
            "",
        ]

        # Add topics in groups of 5 for readability
        for i in range(0, len(topics), 5):
            tag_group = topics[i:i+5]
            instructions.append(f"   {', '.join(tag_group)}")

        instructions.extend([
            "",
            "## 3. Connect Local Repository",
            "",
            "Run these commands in your terminal:",
            "",
            "```bash",
            "# Add remote origin (replace YOUR_USERNAME with your GitHub username)",
            f"git remote add origin https://github.com/YOUR_USERNAME/{self.repo_name}.git",
            "",
            "# Set main as default branch",
            "git branch -M main",
            "",
            "# Push to GitHub",
            "git push -u origin main",
            "```",
            "",
            "## 4. Repository Settings (Optional)",
            "",
            "In your repository settings on GitHub:",
            "- Enable Issues",
            "- Enable Wiki",
            "- Enable Projects",
            "- Set up branch protection rules if needed"
        ])

        return instructions

    def check_prerequisites(self) -> Tuple[bool, List[str]]:
        """
        Check prerequisites for repository creation.

        Returns:
            Tuple[bool, List[str]]: Success status and list of issues

        Time Complexity: O(1)
        """
        issues = []

        # Check if we're in a git repository
        if not (self.project_dir / ".git").exists():
            issues.append(f"❌ Not in a git repository: {self.project_dir}")

        # Check if README.md exists
        if not self.readme_path.exists():
            issues.append(f"❌ README.md not found in: {self.project_dir}")

        # Check if remote origin already exists
        try:
            import subprocess
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            if result.returncode == 0:
                issues.append(
                    "⚠️  Remote 'origin' already exists. You may need to remove it first.")
        except:
            pass  # Git might not be available, but we'll handle that later

        # Check for uncommitted changes
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            if result.stdout.strip():
                issues.append("⚠️  Working directory has uncommitted changes")
        except:
            pass

        return len(issues) == 0, issues

    def validate_metadata(self) -> Tuple[bool, List[str]]:
        """
        Validate that the metadata contains all necessary information.

        Returns:
            Tuple[bool, List[str]]: Success status and list of validation issues

        Time Complexity: O(1)
        """
        issues = []

        if not self.metadata:
            issues.append("❌ Could not load metadata file")
            return False, issues

        if not self.repo_name:
            issues.append("❌ Repository name not specified in metadata")

        if not self.metadata.get("description"):
            issues.append("❌ Repository description not specified in metadata")

        topics = self.metadata.get("topics", [])
        if not topics:
            issues.append("⚠️  No topics specified in metadata")

        return len(issues) == 0, issues

    def check_github_cli_auth(self) -> bool:
        """
        Check if GitHub CLI is available and authenticated.

        Returns:
            bool: True if GitHub CLI is available and authenticated

        Time Complexity: O(1)
        """
        try:
            # Check if GitHub CLI is installed
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False

            # Check if user is authenticated
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0

        except FileNotFoundError:
            return False

    def validate_topics(self, topics: List[str]) -> List[str]:
        """
        Validate and clean topic names according to GitHub requirements.

        Args:
            topics: List of topic names to validate

        Returns:
            List[str]: Validated topic names

        Time Complexity: O(n) where n = number of topics
        """
        valid_topics = []

        for topic in topics:
            # GitHub topic requirements:
            # - lowercase letters, numbers, and hyphens only
            # - max 50 characters
            # - no leading/trailing hyphens

            cleaned_topic = topic.lower().strip()

            # Check length
            if len(cleaned_topic) > 50:
                print(f"⚠️  Topic too long, skipping: {topic}")
                continue

            # Check for invalid characters
            if not all(c.islower() or c.isdigit() or c == '-' for c in cleaned_topic):
                print(
                    f"⚠️  Topic contains invalid characters, skipping: {topic}")
                continue

            # Check for leading/trailing hyphens
            if cleaned_topic.startswith('-') or cleaned_topic.endswith('-'):
                print(
                    f"⚠️  Topic has leading/trailing hyphens, skipping: {topic}")
                continue

            valid_topics.append(cleaned_topic)

        return valid_topics

    def add_topics_to_repository(self, topics: List[str], check_existing: bool = True) -> bool:
        """
        Add topics to the GitHub repository, optionally checking for existing topics.

        Args:
            topics: List of topics to add
            check_existing: Whether to check and avoid duplicate topics

        Returns:
            bool: True if successful, False otherwise

        Time Complexity: O(n) where n = number of topics
        """
        if not topics:
            print("ℹ️  No topics to add")
            return True

        topics_to_add = topics

        if check_existing:
            # Get current topics and filter out duplicates
            current_topics = self.get_current_topics()
            valid_topics = self.validate_topics(topics)

            if not valid_topics:
                print("❌ No valid topics to add")
                return False

            # Display summary before adding
            self.display_topics_summary(current_topics, valid_topics)

            # Only add truly new topics
            truly_new = set(valid_topics) - current_topics
            if not truly_new:
                print("\nℹ️  All topics already exist. Nothing to add.")
                return True

            topics_to_add = list(truly_new)
            print(f"\n📝 Adding {len(topics_to_add)} new topics...")
        else:
            print(f"📝 Adding {len(topics)} topics to repository...")

        try:
            # GitHub CLI command to add topics
            topics_string = ",".join(topics_to_add)
            
            # Try to get the full repository path for the command
            # First, try to get current repository info to determine the proper format
            repo_view_result = subprocess.run([
                "gh", "repo", "view", "--json", "owner,name"
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            if repo_view_result.returncode == 0:
                repo_data = json.loads(repo_view_result.stdout)
                owner = repo_data["owner"]["login"]
                repo_name = repo_data["name"]
                full_repo_path = f"{owner}/{repo_name}"
                
                # Use the full repository path
                result = subprocess.run([
                    "gh", "repo", "edit", full_repo_path, "--add-topic", topics_string
                ], capture_output=True, text=True, cwd=self.project_dir)
            else:
                # Fallback to repository name only (might work in some contexts)
                result = subprocess.run([
                    "gh", "repo", "edit", "--add-topic", topics_string
                ], capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode != 0:
                print(f"❌ Failed to add topics: {result.stderr}")
                return False

            print("✅ Topics added successfully")

            # Verify addition if checking existing topics
            if check_existing:
                return self.verify_topics_addition(topics_to_add)

            return True

        except Exception as e:
            print(f"❌ Error adding topics: {e}")
            return False

    def get_repository_info(self) -> dict:
        """
        Get information about the current repository.

        Returns:
            dict: Repository information including owner and name

        Time Complexity: O(1)
        """
        try:
            # Get repository information
            result = subprocess.run([
                "gh", "repo", "view", "--json", "owner,name,isPrivate,url"
            ], capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode != 0:
                print(
                    "⚠️  Could not get repository info. Make sure you're in a git repository with a GitHub remote.")
                return {}

            repo_info = json.loads(result.stdout)
            return repo_info

        except Exception as e:
            print(f"❌ Error getting repository info: {e}")
            return {}

    def get_current_topics(self) -> Set[str]:
        """
        Get current topics assigned to the repository.

        Returns:
            Set[str]: Current repository topics

        Time Complexity: O(1)
        """
        try:
            result = subprocess.run([
                "gh", "repo", "view", "--json", "repositoryTopics"
            ], capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode != 0:
                print("⚠️  Could not get current topics")
                return set()

            repo_data = json.loads(result.stdout)
            repository_topics = repo_data.get("repositoryTopics", [])
            
            # Handle the case where repositoryTopics might be None
            if repository_topics is None:
                return set()
            
            current_topics = set()
            for topic_item in repository_topics:
                # Handle different possible structures in the API response
                if isinstance(topic_item, dict):
                    if "topic" in topic_item and isinstance(topic_item["topic"], dict):
                        # Structure: {"topic": {"name": "topic-name"}}
                        topic_name = topic_item["topic"].get("name")
                    elif "name" in topic_item:
                        # Structure: {"name": "topic-name"}
                        topic_name = topic_item.get("name")
                    else:
                        # Skip malformed entries
                        continue
                        
                    if topic_name:
                        current_topics.add(topic_name)

            return current_topics

        except Exception as e:
            print(f"❌ Error getting current topics: {e}")
            return set()

    def display_topics_summary(self, current: Set[str], new: List[str]) -> None:
        """
        Display a summary of current and new topics.

        Args:
            current: Current repository topics
            new: New topics to be added

        Time Complexity: O(n) where n = total topics
        """
        print("\n" + "=" * 60)
        print("📋 TOPICS SUMMARY")
        print("=" * 60)

        if current:
            print(f"\n🏷️  Current Topics ({len(current)}):")
            for topic in sorted(current):
                print(f"   • {topic}")
        else:
            print("\n🏷️  Current Topics: None")

        new_topics_set = set(new)
        already_exists = current.intersection(new_topics_set)
        truly_new = new_topics_set - current

        if already_exists:
            print(f"\n✅ Already Exists ({len(already_exists)}):")
            for topic in sorted(already_exists):
                print(f"   • {topic}")

        if truly_new:
            print(f"\n➕ Will Be Added ({len(truly_new)}):")
            for topic in sorted(truly_new):
                print(f"   • {topic}")

        print(f"\n📊 Final Total: {len(current.union(new_topics_set))} topics")

    def verify_topics_addition(self, topics_to_add: List[str]) -> bool:
        """
        Verify that topics were successfully added to the repository.

        Args:
            topics_to_add: List of topics that should have been added

        Returns:
            bool: True if verification passed, False otherwise

        Time Complexity: O(n) where n = number of topics
        """
        print("\n🔍 Verifying topics were added...")
        updated_topics = self.get_current_topics()

        success_count = len(set(topics_to_add).intersection(updated_topics))
        print(
            f"✅ Successfully added {success_count}/{len(topics_to_add)} topics")

        return success_count == len(topics_to_add)

    def create_repository(self) -> bool:
        """
        Create the GitHub repository with all settings, with resume capability.
        
        This method can detect where the process left off and continue from there:
        - If repository exists on GitHub, skip creation
        - If remote origin exists, skip adding it
        - If code is already pushed, skip pushing
        - Continue with remaining steps (topics, settings)

        Returns:
            bool: True if successful, False otherwise

        Time Complexity: O(1)
        """
        description = self.generate_repo_description()
        topics = self.generate_repo_topics()

        print(f"🚀 Creating repository: {self.repo_name}")
        
        # Check current state and determine what steps to perform
        repo_exists_on_github = self._check_repo_exists_on_github()
        has_remote_origin = self._check_has_remote_origin()
        code_is_pushed = self._check_code_is_pushed()
        
        try:
            # Step 1: Create the repository (if not already exists)
            if repo_exists_on_github:
                print("ℹ️  Repository already exists on GitHub, skipping creation...")
            else:
                escaped_description = description.replace('"', '\\"')
                result = subprocess.run([
                    "gh", "repo", "create", self.repo_name,
                    "--private",
                    "--description", escaped_description
                ], capture_output=True, text=True, cwd=self.project_dir)

                if result.returncode != 0:
                    print(f"❌ Failed to create repository: {result.stderr}")
                    return False

                print("✅ Repository created successfully")
                repo_exists_on_github = True

            # Step 2: Add remote origin (if not already exists)
            if has_remote_origin:
                print("ℹ️  Remote origin already exists, skipping...")
                # Verify the remote URL is correct
                existing_url = self._get_current_remote_url()
                print(f"🔍 Current remote URL: {existing_url}")
            else:
                print("🔗 Adding remote origin...")
                
                # First get the GitHub username
                username_result = subprocess.run([
                    "gh", "api", "user", "--jq", ".login"
                ], capture_output=True, text=True, cwd=self.project_dir)
                
                if username_result.returncode != 0:
                    print(f"⚠️  Could not get GitHub username: {username_result.stderr}")
                    print("🔄 Attempting to get username from repository info...")
                    # Try alternative method to get the username
                    repo_view_result = subprocess.run([
                        "gh", "repo", "view", self.repo_name, "--json", "owner"
                    ], capture_output=True, text=True, cwd=self.project_dir)
                    
                    if repo_view_result.returncode == 0:
                        repo_data = json.loads(repo_view_result.stdout)
                        github_username = repo_data["owner"]["login"]
                    else:
                        print("❌ Could not determine GitHub username")
                        return False
                else:
                    github_username = username_result.stdout.strip()
                
                # Construct the repository URL with the actual username
                repo_url = f"https://github.com/{github_username}/{self.repo_name}.git"
                
                # Add the remote origin
                result = subprocess.run([
                    "git", "remote", "add", "origin", repo_url
                ], capture_output=True, text=True, cwd=self.project_dir)

                if result.returncode != 0:
                    print(f"⚠️  Could not add remote origin: {result.stderr}")
                    print(f"🔍 Attempted URL: {repo_url}")
                    # Don't return False here, try to continue with other steps
                else:
                    print(f"✅ Remote origin added: {repo_url}")
                    has_remote_origin = True

            # Step 3: Set main as default branch
            print("🌿 Setting main as default branch...")
            subprocess.run(["git", "branch", "-M", "main"],
                           capture_output=True, text=True, cwd=self.project_dir)

            # Step 4: Push to GitHub (if not already pushed)
            if code_is_pushed:
                print("ℹ️  Code already pushed to GitHub, skipping...")
            else:
                print("📤 Pushing to GitHub...")
                result = subprocess.run([
                    "git", "push", "-u", "origin", "main"
                ], capture_output=True, text=True, cwd=self.project_dir)

                if result.returncode != 0:
                    print(f"❌ Failed to push to GitHub: {result.stderr}")
                    print("🔍 Checking if remote origin is properly configured...")
                    
                    # Try to diagnose the issue
                    remote_check = subprocess.run([
                        "git", "remote", "-v"
                    ], capture_output=True, text=True, cwd=self.project_dir)
                    
                    if remote_check.returncode == 0:
                        print(f"📋 Current remotes:\n{remote_check.stdout}")
                    
                    # If we have a remote but can't push, might be authentication issue
                    if has_remote_origin:
                        print("💡 Possible solutions:")
                        print("   1. Check GitHub CLI authentication: gh auth status")
                        print("   2. Verify repository permissions")
                        print("   3. Try: gh auth refresh")
                    
                    return False

                print("✅ Code pushed successfully")
                code_is_pushed = True

            # Step 5: Add topics (always attempt, as topics might have changed)
            if topics:
                print("🏷️  Adding repository topics...")
                # For resume scenarios, check existing topics to avoid duplicates
                valid_topics = self.validate_topics(topics)
                if valid_topics:
                    # Use existing topic checking since repository already exists
                    if not self.add_topics_to_repository(valid_topics, check_existing=True):
                        print("⚠️  Repository setup complete but topics failed to add")
                else:
                    print("⚠️  No valid topics to add")
            else:
                print("ℹ️  No topics specified in metadata")

            # Step 6: Set repository settings (always attempt)
            print("⚙️  Configuring repository settings...")
            
            # Get the repository owner/name for the edit command
            repo_info_result = subprocess.run([
                "gh", "repo", "view", self.repo_name, "--json", "owner,name"
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            if repo_info_result.returncode == 0:
                repo_info_data = json.loads(repo_info_result.stdout)
                owner = repo_info_data["owner"]["login"]
                repo_name = repo_info_data["name"]
                full_repo_path = f"{owner}/{repo_name}"
                
                settings_result = subprocess.run([
                    "gh", "repo", "edit", full_repo_path,
                    "--enable-issues",
                    "--enable-wiki",
                    "--enable-projects"
                ], capture_output=True, text=True, cwd=self.project_dir)
                
                if settings_result.returncode != 0:
                    print(f"⚠️  Could not configure some repository settings: {settings_result.stderr}")
                else:
                    print("✅ Repository settings configured")
            else:
                print("⚠️  Could not get repository info for settings configuration")
                # Fallback: try with just the repo name (might work in some contexts)
                settings_result = subprocess.run([
                    "gh", "repo", "edit", self.repo_name,
                    "--enable-issues",
                    "--enable-wiki",
                    "--enable-projects"
                ], capture_output=True, text=True, cwd=self.project_dir)
                
                if settings_result.returncode != 0:
                    print(f"⚠️  Fallback repository settings also failed: {settings_result.stderr}")
                else:
                    print("✅ Repository settings configured (fallback)")

            # Step 7: Show repository URL
            result = subprocess.run([
                "gh", "repo", "view", self.repo_name, "--json", "url"
            ], capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode == 0:
                repo_data = json.loads(result.stdout)
                repo_url = repo_data.get("url", "")
                print(f"🌐 Repository URL: {repo_url}")

            print("\n🎉 Repository setup completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error during repository setup: {e}")
            return False

    def _check_repo_exists_on_github(self) -> bool:
        """
        Check if the repository already exists on GitHub.
        
        Returns:
            bool: True if repository exists on GitHub
        """
        try:
            result = subprocess.run([
                "gh", "repo", "view", self.repo_name
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            return result.returncode == 0
        except Exception:
            return False

    def _check_has_remote_origin(self) -> bool:
        """
        Check if the local repository has a remote origin configured.
        
        Returns:
            bool: True if remote origin exists
        """
        try:
            result = subprocess.run([
                "git", "remote", "get-url", "origin"
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            return result.returncode == 0
        except Exception:
            return False

    def _get_current_remote_url(self) -> str:
        """
        Get the current remote origin URL.
        
        Returns:
            str: Current remote URL or empty string if not found
        """
        try:
            result = subprocess.run([
                "git", "remote", "get-url", "origin"
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception:
            return ""

    def _check_code_is_pushed(self) -> bool:
        """
        Check if the local code has been pushed to the remote repository.
        
        Returns:
            bool: True if code appears to be pushed to remote
        """
        try:
            # Check if we can fetch from origin (indicates remote exists and is accessible)
            fetch_result = subprocess.run([
                "git", "fetch", "origin", "main"
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            if fetch_result.returncode != 0:
                return False
            
            # Check if local main is up to date with origin/main
            status_result = subprocess.run([
                "git", "status", "-b", "--porcelain"
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            if status_result.returncode == 0:
                # Look for indicators that we're behind or ahead
                status_output = status_result.stdout
                # If we see "ahead" or "behind" it means we have a tracking relationship
                # If there's no such indication and fetch worked, code is likely pushed
                if "ahead" not in status_output and "behind" not in status_output:
                    return True
                    
            return False
        except Exception:
            return False

    def run(self) -> bool:
        """
        Execute the repository creation helper process.

        Returns:
            bool: True if successful, False otherwise

        Time Complexity: O(1)
        """
        print("🚀 GitHub Repository Creation Helper")
        print("=" * 60)

        # Validate metadata
        metadata_valid, metadata_issues = self.validate_metadata()
        if metadata_issues:
            print("📋 Metadata validation:")
            for issue in metadata_issues:
                print(f"   {issue}")
            print()

        if not metadata_valid:
            print("❌ Cannot proceed without valid metadata")
            return False

        # Check prerequisites
        success, issues = self.check_prerequisites()

        if issues:
            print("⚠️  Prerequisites check:")
            for issue in issues:
                print(f"   {issue}")
            print()

        # Generate repository information
        description = self.generate_repo_description()
        topics = self.generate_repo_topics()

        print(f"📋 Repository Information (from {self.metadata_file}):")
        print(f"   Name: {self.repo_name}")
        print(f"   Type: Private repository")
        print(f"   Description: {description[:100]}...")
        print(f"   Topics: {len(topics)} topics")
        print()

        # Check if GitHub CLI is available
        gh_available = self.check_github_cli_auth()

        print("🔧 Setup Options:")
        print()

        if gh_available:
            print("✅ GitHub CLI detected - Automated setup available")
            print()
            print("Option 1: Direct Repository Creation (Recommended)")
            print("-" * 50)
            print("This will create a new repository directly using the script.")
            print()

            # Ask user for direct creation
            response = input(
                "Do you want to create the repository now? (Y/n): ").strip().lower()

            if response in ['', 'y', 'yes']:
                print("\n🚀 Starting repository creation...")
                return self.create_repository()

            print("\nOption 2: Manage Existing Repository Topics")
            print("-" * 42)
            print("Add/update topics for an existing repository.")
            print()

            # Ask user for topic management
            response = input(
                "Do you want to manage topics for an existing repository? (y/N): ").strip().lower()

            if response in ['y', 'yes']:
                print("\n🏷️  Starting topic management...")
                return self.manage_existing_repository_topics()

            print("\nOption 3: Manual Commands")
            print("-" * 25)
            print("Here are the commands you can run manually:")
            print()

            commands = self.generate_github_cli_commands()
            for command in commands:
                if command.startswith("#"):
                    print(f"\033[36m{command}\033[0m")  # Cyan for comments
                elif command.strip():
                    print(f"\033[92m{command}\033[0m")  # Green for commands
                else:
                    print(command)

        else:
            print("❌ GitHub CLI not detected")
            print("   Install with: https://cli.github.com/")

        print()
        print("Option 4: Manual Setup (Web Interface)")
        print("-" * 40)

        manual_instructions = self.generate_manual_setup_instructions()
        manual_file = self.project_dir / "GITHUB_SETUP.md"

        with open(manual_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(manual_instructions))

        print(f"📄 Manual instructions saved to: {manual_file}")
        print()

        # Show next steps
        print("🎯 Next Steps:")
        if gh_available:
            print("   1. Re-run this script and choose repository creation")
            print("   2. Use option 2 to manage topics for existing repositories")
            print("   3. Or follow the manual commands shown above")
        else:
            print("   1. Install GitHub CLI: https://cli.github.com/")
            print("   2. Authenticate: gh auth login")
            print("   3. Re-run this script for automated creation/management")

        return True

    @classmethod
    def add_topics_from_metadata(cls, metadata_file: str = None, repo_name: str = None, project_dir: str = None) -> bool:
        """
        Class method to add topics from metadata file without user interaction.

        Args:
            metadata_file: Path to the metadata JSON file
            repo_name: Repository name (optional, will be read from metadata)
            project_dir: Path to the project directory (optional, defaults to current directory)

        Returns:
            bool: True if successful, False otherwise

        Time Complexity: O(n) where n = number of topics
        """
        creator = cls(metadata_file=metadata_file, project_dir=project_dir)

        # Override repo name if provided
        if repo_name:
            creator.repo_name = repo_name

        # Check if metadata was loaded successfully
        if not creator.metadata:
            return False

        if not creator.repo_name:
            print("❌ Repository name not found in metadata")
            return False

        topics = creator.generate_repo_topics()
        if not topics:
            print("ℹ️  No topics found in metadata to add")
            return True

        # Check prerequisites
        if not creator.check_github_cli_auth():
            print("❌ GitHub CLI not available or not authenticated")
            return False

        # Get repository information
        repo_info = creator.get_repository_info()
        if not repo_info:
            return False

        # Add topics with existing topic checking
        print(
            f"📝 Adding topics to {repo_info.get('name', creator.repo_name)}...")
        return creator.add_topics_to_repository(topics, check_existing=True)

    def manage_existing_repository_topics(self) -> bool:
        """
        Manage topics for an existing repository with comprehensive checking.

        Returns:
            bool: True if successful, False otherwise

        Time Complexity: O(n) where n = number of topics
        """
        print("🏷️  Managing Topics for Existing Repository")
        print("=" * 60)

        # Validate metadata
        metadata_valid, metadata_issues = self.validate_metadata()
        if metadata_issues:
            print("📋 Metadata validation:")
            for issue in metadata_issues:
                print(f"   {issue}")
            print()

        if not metadata_valid:
            print("❌ Cannot proceed without valid metadata")
            return False

        # Check GitHub CLI authentication
        if not self.check_github_cli_auth():
            print("❌ GitHub CLI not available or not authenticated")
            return False

        # Get repository information
        repo_info = self.get_repository_info()
        if not repo_info:
            print("❌ Could not get repository information")
            return False

        print(
            f"\n📁 Repository: {repo_info['owner']['login']}/{repo_info['name']}")
        print(
            f"🔒 Privacy: {'Private' if repo_info['isPrivate'] else 'Public'}")
        print(f"🌐 URL: {repo_info['url']}")

        # Get topics from metadata
        topics = self.generate_repo_topics()
        if not topics:
            print("❌ No topics found in metadata")
            return False

        print(f"\n📄 Metadata file: {self.metadata_file}")
        print(f"🏷️  Topics to process: {len(topics)}")

        # Use enhanced topic management with existing topic checking
        return self.add_topics_to_repository(topics, check_existing=True)


def main():
    """
    Main entry point for the script.

    Time Complexity: O(1)
    """
    parser = argparse.ArgumentParser(
        description="Create GitHub repository and manage topics from metadata file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default)
  python create_github_repo.py

  # Create repository directly
  python create_github_repo.py --create

  # Manage topics for existing repository
  python create_github_repo.py --manage-topics

  # Use custom metadata file
  python create_github_repo.py --metadata my_project.json --create

  # Work on a different project directory
  python create_github_repo.py --project-dir /path/to/project --create

  # Add topics programmatically (for automation)
  python create_github_repo.py --add-topics-only
        """
    )
    parser.add_argument(
        "--metadata",
        type=str,
        help="Path to metadata JSON file (default: github_repo_metadata.json)"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        help="Path to the project directory (default: current working directory)"
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create repository directly without interactive prompts"
    )
    parser.add_argument(
        "--manage-topics",
        action="store_true",
        help="Manage topics for existing repository"
    )
    parser.add_argument(
        "--add-topics-only",
        action="store_true",
        help="Add topics from metadata without user interaction (for automation)"
    )

    args = parser.parse_args()

    try:
        creator = GitHubRepoCreator(metadata_file=args.metadata, project_dir=args.project_dir)

        # Handle different modes
        if args.create:
            print("🚀 Creating repository directly from command line...")
            success = creator.create_repository()
        elif args.manage_topics:
            print("🏷️  Managing topics for existing repository...")
            success = creator.manage_existing_repository_topics()
        elif args.add_topics_only:
            print("📝 Adding topics from metadata (automation mode)...")
            success = GitHubRepoCreator.add_topics_from_metadata(
                metadata_file=args.metadata, project_dir=args.project_dir)
        else:
            # Interactive mode
            success = creator.run()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
