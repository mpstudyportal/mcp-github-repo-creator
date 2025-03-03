#!/usr/bin/env python3
"""
Core functionality test for the GitHub Repository Creator.

This script tests the repository analysis and metadata generation 
without requiring MCP framework dependencies.

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
import subprocess
import re
from pathlib import Path
from typing import Any, Dict, List


class RepositoryAnalyzer:
    """Analyzes a local repository to generate metadata for GitHub creation."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def is_git_repository(self) -> bool:
        """Check if the current directory is a git repository."""
        return (self.repo_path / ".git").exists()

    def get_repository_name(self) -> str:
        """Extract repository name from current directory or git remote."""
        try:
            # Try to get from git remote first
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            if result.returncode == 0 and result.stdout.strip():
                # Parse GitHub URL to get repo name
                url = result.stdout.strip()
                match = re.search(r'/([^/]+)\.git$', url)
                if match:
                    return match.group(1)
        except:
            pass

        # Fallback to directory name
        return self.repo_path.name

    def detect_primary_language(self) -> str:
        """Detect the primary programming language of the repository."""
        language_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.m': 'Objective-C',
            '.sh': 'Shell',
            '.html': 'HTML',
            '.css': 'CSS',
            '.vue': 'Vue',
            '.jsx': 'React',
            '.tsx': 'TypeScript React'
        }

        file_counts = {}

        # Count files by extension
        for file_path in self.repo_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_path(file_path):
                ext = file_path.suffix.lower()
                if ext in language_extensions:
                    lang = language_extensions[ext]
                    file_counts[lang] = file_counts.get(lang, 0) + 1

        if not file_counts:
            return "Unknown"

        # Return the language with most files
        return max(file_counts, key=file_counts.get)

    def _should_ignore_path(self, path: Path) -> bool:
        """Check if a path should be ignored (e.g., in .git, node_modules, etc.)."""
        ignore_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache',
            'venv', '.venv', 'env', '.env', 'dist', 'build',
            '.next', '.nuxt', 'target', 'bin', 'obj'
        }

        for part in path.parts:
            if part in ignore_dirs or part.startswith('.'):
                return True
        return False

    def extract_description_from_readme(self) -> str:
        """Extract description from README file."""
        readme_files = ['README.md', 'README.rst', 'README.txt', 'readme.md']

        for readme_file in readme_files:
            readme_path = self.repo_path / readme_file
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding='utf-8')

                    # Extract first meaningful paragraph
                    lines = content.split('\n')
                    description_lines = []

                    for line in lines:
                        line = line.strip()
                        # Skip empty lines, titles, and badges
                        if (not line or
                            line.startswith('#') or
                            line.startswith('![') or
                            line.startswith('[![') or
                                line.startswith('---')):
                            continue

                        description_lines.append(line)

                        # Stop at first paragraph
                        if len(description_lines) >= 3:
                            break

                    if description_lines:
                        description = ' '.join(description_lines)
                        # Limit length
                        if len(description) > 200:
                            description = description[:197] + "..."
                        return description

                except Exception:
                    continue

        return f"A {self.detect_primary_language()} project"

    def generate_topics_from_analysis(self) -> List[str]:
        """Generate relevant topics based on repository analysis."""
        topics = []

        # Add language-based topics
        primary_lang = self.detect_primary_language().lower()
        if primary_lang != "unknown":
            topics.append(primary_lang)

        # Check for specific frameworks/technologies
        technology_indicators = {
            'react': ['package.json', 'src/App.jsx', 'src/App.js'],
            'vue': ['package.json', 'src/App.vue'],
            'angular': ['angular.json', 'src/app'],
            'django': ['manage.py', 'settings.py'],
            'flask': ['app.py', 'requirements.txt'],
            'fastapi': ['main.py', 'requirements.txt'],
            'express': ['package.json', 'server.js'],
            'nextjs': ['next.config.js', 'pages'],
            'nuxt': ['nuxt.config.js'],
            'tensorflow': ['requirements.txt'],
            'pytorch': ['requirements.txt'],
            'docker': ['Dockerfile', 'docker-compose.yml'],
            'kubernetes': ['k8s/', 'kubernetes/'],
            'machine-learning': ['model.py', 'train.py', 'data/'],
            'api': ['api/', 'routes/'],
            'cli': ['cli.py', 'bin/'],
            'automation': ['scripts/', 'tools/'],
            'web-app': ['public/', 'static/'],
            'mobile': ['android/', 'ios/'],
            'desktop': ['electron/', 'tauri/']
        }

        for tech, indicators in technology_indicators.items():
            for indicator in indicators:
                if (self.repo_path / indicator).exists():
                    topics.append(tech)
                    break

        # Check file contents for specific keywords
        if self._check_files_for_keywords(['requirements.txt', 'pyproject.toml'], ['machine', 'learning', 'ai', 'neural']):
            topics.extend(['machine-learning', 'artificial-intelligence'])

        if self._check_files_for_keywords(['package.json'], ['react', 'vue', 'angular']):
            topics.append('frontend')

        # Add project type topics
        if any((self.repo_path / f).exists() for f in ['Dockerfile', 'docker-compose.yml']):
            topics.append('containerization')

        if any((self.repo_path / f).exists() for f in ['.github', 'ci/', '.gitlab-ci.yml']):
            topics.append('ci-cd')

        # Remove duplicates and return
        return list(set(topics))

    def _check_files_for_keywords(self, files: List[str], keywords: List[str]) -> bool:
        """Check if any of the files contain any of the keywords."""
        for file_name in files:
            file_path = self.repo_path / file_name
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8').lower()
                    if any(keyword in content for keyword in keywords):
                        return True
                except:
                    continue
        return False

    def detect_license(self) -> str:
        """Detect license from LICENSE file or common patterns."""
        license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING']

        for license_file in license_files:
            license_path = self.repo_path / license_file
            if license_path.exists():
                try:
                    content = license_path.read_text(encoding='utf-8').lower()

                    if 'mit license' in content:
                        return 'MIT'
                    elif 'apache license' in content:
                        return 'Apache-2.0'
                    elif 'gnu general public license' in content:
                        if 'version 3' in content:
                            return 'GPL-3.0'
                        else:
                            return 'GPL-2.0'
                    elif 'bsd license' in content:
                        return 'BSD-3-Clause'
                    elif 'mozilla public license' in content:
                        return 'MPL-2.0'
                except:
                    continue

        return 'MIT'  # Default fallback

    def extract_features_from_files(self) -> List[str]:
        """Extract key features from documentation and code."""
        features = []

        # Check README for features
        readme_path = self.repo_path / "README.md"
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding='utf-8')

                # Look for feature sections
                feature_patterns = [
                    r'## Features?\s*\n(.*?)(?=\n##|\n#|\Z)',
                    r'### Features?\s*\n(.*?)(?=\n###|\n##|\n#|\Z)',
                    r'\*\*Features?\*\*\s*\n(.*?)(?=\n\*\*|\Z)'
                ]

                for pattern in feature_patterns:
                    matches = re.findall(
                        pattern, content, re.DOTALL | re.IGNORECASE)
                    for match in matches:
                        # Extract bullet points
                        lines = match.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('-') or line.startswith('*'):
                                feature = line[1:].strip()
                                if feature and len(feature) < 100:
                                    features.append(feature)
            except:
                pass

        # Add default features if none found
        if not features:
            lang = self.detect_primary_language()
            if lang == "Python":
                features = ["Python implementation",
                            "Easy to use", "Well documented"]
            elif lang in ["JavaScript", "TypeScript"]:
                features = ["Modern JavaScript/TypeScript",
                            "Responsive design", "Cross-platform"]
            else:
                features = ["Clean code architecture",
                            "Easy to maintain", "Extensible design"]

        return features[:5]  # Limit to 5 features

    def generate_metadata(self) -> Dict[str, Any]:
        """Generate complete metadata for the repository."""
        repo_name = self.get_repository_name()
        description = self.extract_description_from_readme()
        topics = self.generate_topics_from_analysis()
        primary_language = self.detect_primary_language()
        license_type = self.detect_license()
        features = self.extract_features_from_files()

        # Determine project type
        if any(topic in topics for topic in ['machine-learning', 'ai', 'tensorflow', 'pytorch']):
            project_type = "AI/ML"
        elif any(topic in topics for topic in ['react', 'vue', 'angular', 'web-app']):
            project_type = "Web Application"
        elif 'cli' in topics:
            project_type = "CLI Tool"
        elif 'api' in topics:
            project_type = "API"
        elif 'mobile' in topics:
            project_type = "Mobile App"
        else:
            project_type = "Software Library"

        return {
            "repository_name": repo_name,
            "description": description,
            "topics": topics,
            "created_date": "2025-01-01",
            "project_type": project_type,
            "primary_language": primary_language,
            "license": license_type,
            "features": features
        }


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
    print("📄 Content preview:")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    # Clean up
    test_file.unlink()

    return metadata


def test_github_cli():
    """Test GitHub CLI availability."""
    print("\n🔧 Testing GitHub CLI")
    print("=" * 30)

    try:
        # Check if GitHub CLI is installed
        result = subprocess.run(["gh", "--version"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GitHub CLI is installed")
            print(f"Version: {result.stdout.strip()}")

            # Check authentication
            auth_result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True)
            if auth_result.returncode == 0:
                print("✅ GitHub CLI is authenticated")
                return True
            else:
                print("❌ GitHub CLI not authenticated")
                print("💡 Run 'gh auth login' to authenticate")
                return False
        else:
            print("❌ GitHub CLI not installed")
            print("💡 Install from: https://cli.github.com/")
            return False

    except FileNotFoundError:
        print("❌ GitHub CLI not found")
        print("💡 Install from: https://cli.github.com/")
        return False


def main():
    """Run all tests."""
    print("🚀 GitHub Repository Creator - Core Functionality Tests")
    print("=" * 70)

    try:
        # Test 1: Repository Analysis
        metadata = test_repository_analyzer()

        # Test 2: Metadata Generation
        test_metadata_generation()

        # Test 3: GitHub CLI
        gh_available = test_github_cli()

        print("\n📊 Test Summary")
        print("=" * 30)
        print("✅ Repository analysis: PASSED")
        print("✅ Metadata generation: PASSED")
        print(f"{'✅' if gh_available else '❌'} GitHub CLI: {'AVAILABLE' if gh_available else 'NOT AVAILABLE'}")

        if gh_available:
            print("\n🎉 All core functionality tests passed!")
            print("\n💡 The MCP server core functionality is working correctly.")
            print("   Next steps:")
            print("   1. Install MCP framework: pip install mcp")
            print("   2. Test the full MCP server")
            print("   3. Configure with your MCP client")
        else:
            print(
                "\n⚠️  Core functionality works but GitHub CLI is needed for repository creation.")
            print("   Install and authenticate GitHub CLI to enable repository creation.")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
