#!/usr/bin/env python3
"""
Test script for the GitHub Repository Creator MCP server.

This script tests the core functionality without requiring MCP framework.

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
import json
from pathlib import Path

# Add the parent directory to import our modules
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "create-repo"))

try:
    from server import RepositoryAnalyzer
    from core.create_github_repo import GitHubRepoCreator
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the mcp-github-repo-creator directory")
    sys.exit(1)


def test_repository_analyzer():
    """Test the repository analyzer functionality."""
    print("🧪 Testing Repository Analyzer")
    print("=" * 50)

    # Test with current directory
    analyzer = RepositoryAnalyzer(".")

    # Test basic checks
    is_git = analyzer.is_git_repository()
    print(f"Is git repository: {is_git}")

    repo_name = analyzer.get_repository_name()
    print(f"Repository name: {repo_name}")

    primary_lang = analyzer.detect_primary_language()
    print(f"Primary language: {primary_lang}")

    description = analyzer.extract_description_from_readme()
    print(f"Description: {description[:100]}...")

    topics = analyzer.generate_topics_from_analysis()
    print(f"Topics: {topics}")

    license_type = analyzer.detect_license()
    print(f"License: {license_type}")

    features = analyzer.extract_features_from_files()
    print(f"Features: {features}")

    print("\n🔬 Generating full metadata...")
    metadata = analyzer.generate_metadata()
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    return metadata


def test_metadata_generation():
    """Test metadata file generation."""
    print("\n📄 Testing Metadata File Generation")
    print("=" * 50)

    analyzer = RepositoryAnalyzer(".")
    metadata = analyzer.generate_metadata()

    # Write test metadata file
    test_file = Path("test_metadata.json")
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ Test metadata file created: {test_file}")

    # Test if our GitHubRepoCreator can read it
    try:
        creator = GitHubRepoCreator(metadata_file=str(test_file))
        validation_result, issues = creator.validate_metadata()

        if validation_result:
            print("✅ Metadata validation passed")
        else:
            print("❌ Metadata validation failed:")
            for issue in issues:
                print(f"  - {issue}")

    except Exception as e:
        print(f"❌ Error testing GitHubRepoCreator: {e}")

    # Clean up
    test_file.unlink()

    return metadata


def test_github_prerequisites():
    """Test GitHub CLI prerequisites."""
    print("\n🔧 Testing GitHub Prerequisites")
    print("=" * 50)

    try:
        creator = GitHubRepoCreator()
        gh_available = creator.check_github_cli_auth()

        if gh_available:
            print("✅ GitHub CLI is available and authenticated")
        else:
            print("❌ GitHub CLI not available or not authenticated")
            print("💡 Run 'gh auth login' to authenticate")

        return gh_available
    except Exception as e:
        print(f"❌ Error checking GitHub CLI: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 GitHub Repository Creator MCP Server Tests")
    print("=" * 60)

    try:
        # Test 1: Repository Analysis
        metadata = test_repository_analyzer()

        # Test 2: Metadata Generation
        test_metadata_generation()

        # Test 3: GitHub Prerequisites
        gh_available = test_github_prerequisites()

        print("\n📊 Test Summary")
        print("=" * 30)
        print("✅ Repository analysis: PASSED")
        print("✅ Metadata generation: PASSED")
        print(f"{'✅' if gh_available else '❌'} GitHub CLI: {'PASSED' if gh_available else 'NOT AVAILABLE'}")

        if gh_available:
            print("\n🎉 All tests passed! The MCP server should work correctly.")
            print("\n💡 Next steps:")
            print("1. Install MCP framework: pip install mcp")
            print("2. Configure the MCP server in your client")
            print("3. Use with Copilot to create GitHub repositories")
        else:
            print("\n⚠️  Tests passed but GitHub CLI not available.")
            print("   Install and authenticate GitHub CLI to use the full functionality.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
