#!/usr/bin/env python3
"""
Repository Analyzer module for GitHub repository creation MCP server.

This module contains the RepositoryAnalyzer class that analyzes local 
repositories to extract metadata for GitHub repository creation.

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
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

class RepositoryAnalyzer:
    """Analyzes a local repository to generate metadata for GitHub creation."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def is_git_repository(self) -> bool:
        return (self.repo_path / ".git").exists()

    def get_repository_name(self) -> str:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                repo_name = url.split('/')[-1].replace('.git', '')
                return repo_name
        except:
            pass
        return self.repo_path.name.lower().replace(' ', '-').replace('_', '-')

    def detect_primary_language(self) -> str:
        language_extensions = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.jsx': 'JavaScript', '.tsx': 'TypeScript',
            '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.cs': 'C#', '.php': 'PHP', '.rb': 'Ruby', '.go': 'Go',
            '.rs': 'Rust', '.swift': 'Swift', '.kt': 'Kotlin', '.scala': 'Scala', '.html': 'HTML', '.css': 'CSS',
            '.scss': 'SCSS', '.vue': 'Vue', '.dart': 'Dart', '.r': 'R', '.m': 'MATLAB', '.sh': 'Shell'
        }
        file_counts = {}
        for file_path in self.repo_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_path(file_path):
                ext = file_path.suffix.lower()
                if ext in language_extensions:
                    lang = language_extensions[ext]
                    file_counts[lang] = file_counts.get(lang, 0) + 1
        if not file_counts:
            return "Unknown"
        return max(file_counts, key=file_counts.get)

    def _should_ignore_path(self, path: Path) -> bool:
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
        readme_files = ['README.md', 'README.rst', 'README.txt', 'readme.md']
        for readme_file in readme_files:
            readme_path = self.repo_path / readme_file
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    description_lines = []
                    for line in lines:
                        line = line.strip()
                        if (not line or line.startswith('#') or line.startswith('![') or line.startswith('[![') or line.startswith('---')):
                            continue
                        description_lines.append(line)
                        if len(description_lines) >= 2 or len(' '.join(description_lines)) > 150:
                            break
                    if description_lines:
                        description = ' '.join(description_lines)
                        description = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', description)
                        description = re.sub(r'\*\*([^*]+)\*\*', r'\1', description)
                        description = re.sub(r'\*([^*]+)\*', r'\1', description)
                        return description[:300] + ("..." if len(description) > 300 else "")
                except Exception:
                    continue
        return f"A {self.detect_primary_language()} project"

    def detect_license(self) -> str:
        license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'license', 'license.txt']
        for license_file in license_files:
            license_path = self.repo_path / license_file
            if license_path.exists():
                try:
                    content = license_path.read_text(encoding='utf-8').upper()
                    if 'MIT' in content:
                        return 'MIT'
                    elif 'APACHE' in content:
                        return 'Apache-2.0'
                    elif 'GPL' in content:
                        if 'VERSION 3' in content:
                            return 'GPL-3.0'
                        return 'GPL-2.0'
                    elif 'BSD' in content:
                        return 'BSD'
                except:
                    pass
        package_json = self.repo_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'license' in data:
                        return data['license']
            except:
                pass
        return "MIT"

    def generate_topics(self) -> List[str]:
        topics = set()
        primary_lang = self.detect_primary_language().lower()
        if primary_lang != 'unknown':
            topics.add(primary_lang)
        package_files = {
            'package.json': self._detect_js_frameworks,
            'requirements.txt': self._detect_python_frameworks,
            'Pipfile': self._detect_python_frameworks,
            'pyproject.toml': self._detect_python_frameworks,
            'Cargo.toml': self._detect_rust_frameworks,
            'go.mod': self._detect_go_frameworks
        }
        for file_name, detector in package_files.items():
            file_path = self.repo_path / file_name
            if file_path.exists():
                framework_topics = detector(file_path)
                topics.update(framework_topics)
        structure_topics = self._detect_from_structure()
        topics.update(structure_topics)
        topics = [t for t in topics if t and len(t) > 1]
        return sorted(list(topics))[:20]

    def _detect_js_frameworks(self, package_json_path: Path) -> List[str]:
        topics = []
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            framework_map = {
                'react': 'react', 'next': 'nextjs', 'vue': 'vue', 'angular': 'angular', 'express': 'express',
                'fastify': 'fastify', 'koa': 'koa', 'typescript': 'typescript', 'webpack': 'webpack', 'vite': 'vite',
                'jest': 'testing', 'cypress': 'testing', 'eslint': 'linting', 'prettier': 'formatting'
            }
            for dep in dependencies:
                for keyword, topic in framework_map.items():
                    if keyword in dep.lower():
                        topics.append(topic)
        except:
            pass
        return topics

    def _detect_python_frameworks(self, requirements_path: Path) -> List[str]:
        topics = []
        try:
            if requirements_path.name == 'pyproject.toml':
                content = requirements_path.read_text(encoding='utf-8')
                deps_text = content.lower()
            else:
                content = requirements_path.read_text(encoding='utf-8')
                deps_text = content.lower()
            framework_map = {
                'django': 'django', 'flask': 'flask', 'fastapi': 'fastapi', 'tornado': 'tornado',
                'pandas': 'data-science', 'numpy': 'data-science', 'tensorflow': 'machine-learning',
                'pytorch': 'machine-learning', 'scikit-learn': 'machine-learning', 'opencv': 'computer-vision',
                'requests': 'api', 'click': 'cli', 'typer': 'cli'
            }
            for keyword, topic in framework_map.items():
                if keyword in deps_text:
                    topics.append(topic)
        except:
            pass
        return topics

    def _detect_rust_frameworks(self, cargo_path: Path) -> List[str]:
        topics = ['rust']
        try:
            content = cargo_path.read_text(encoding='utf-8')
            deps_text = content.lower()
            framework_map = {
                'actix': 'web-framework', 'warp': 'web-framework', 'rocket': 'web-framework', 'tokio': 'async',
                'serde': 'serialization', 'clap': 'cli'
            }
            for keyword, topic in framework_map.items():
                if keyword in deps_text:
                    topics.append(topic)
        except:
            pass
        return topics

    def _detect_go_frameworks(self, go_mod_path: Path) -> List[str]:
        topics = ['go', 'golang']
        try:
            content = go_mod_path.read_text(encoding='utf-8')
            deps_text = content.lower()
            framework_map = {
                'gin': 'web-framework', 'echo': 'web-framework', 'fiber': 'web-framework', 'grpc': 'grpc', 'cobra': 'cli'
            }
            for keyword, topic in framework_map.items():
                if keyword in deps_text:
                    topics.append(topic)
        except:
            pass
        return topics

    def _detect_from_structure(self) -> List[str]:
        topics = []
        directories = [d.name.lower() for d in self.repo_path.iterdir() if d.is_dir()]
        structure_map = {
            'src': 'library', 'lib': 'library', 'bin': 'cli', 'cmd': 'cli', 'api': 'api', 'web': 'web-app',
            'frontend': 'frontend', 'backend': 'backend', 'server': 'server', 'client': 'client', 'docs': 'documentation',
            'tests': 'testing', 'test': 'testing', 'examples': 'examples', 'demo': 'demo'
        }
        for directory in directories:
            if directory in structure_map:
                topics.append(structure_map[directory])
        return topics

    def detect_project_type(self) -> str:
        if (self.repo_path / 'package.json').exists():
            package_json = self.repo_path / 'package.json'
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    if 'next' in deps or 'nuxt' in deps:
                        return "Web Application"
                    elif 'react' in deps or 'vue' in deps or 'angular' in deps:
                        return "Web Application"
                    elif 'express' in deps or 'fastify' in deps or 'koa' in deps:
                        return "API/Backend"
                    elif any(cli in deps for cli in ['commander', 'yargs', 'inquirer']):
                        return "CLI Tool"
            except:
                pass
        if any((self.repo_path / f).exists() for f in ['requirements.txt', 'pyproject.toml', 'setup.py']):
            if any((self.repo_path / f).exists() for f in ['app.py', 'main.py', 'manage.py']):
                return "Web Application"
            elif (self.repo_path / 'setup.py').exists():
                return "Library/Package"
        if (self.repo_path / 'bin').exists() or (self.repo_path / 'cmd').exists():
            return "CLI Tool"
        if any((self.repo_path / f).exists() for f in ['index.html', 'public', 'static']):
            return "Web Application"
        primary_lang = self.detect_primary_language()
        if primary_lang in ['JavaScript', 'TypeScript']:
            return "Web Application"
        elif primary_lang == 'Python':
            return "Python Project"
        elif primary_lang in ['Go', 'Rust', 'C', 'C++']:
            return "CLI Tool"
        return "Software Project"

    def extract_features(self) -> List[str]:
        features = []
        readme_files = ['README.md', 'README.rst', 'README.txt']
        for readme_file in readme_files:
            readme_path = self.repo_path / readme_file
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding='utf-8')
                    features_section = re.search(
                        r'(?:features|capabilities|functionality):\s*\n(.*?)(?:\n\n|\n#+|\n-{3,}|\Z)',
                        content,
                        re.IGNORECASE | re.DOTALL
                    )
                    if features_section:
                        feature_text = features_section.group(1)
                        for line in feature_text.split('\n'):
                            line = line.strip()
                            if line.startswith(('- ', '* ', '+ ', '• ')):
                                feature = line[2:].strip()
                                if feature and len(feature) > 5:
                                    features.append(feature)
                except:
                    pass
        if not features:
            project_type = self.detect_project_type()
            if project_type == "Web Application":
                features = ["Modern web interface", "Responsive design", "User-friendly experience"]
            elif project_type == "API/Backend":
                features = ["RESTful API", "Database integration", "Authentication system"]
            elif project_type == "CLI Tool":
                features = ["Command-line interface", "Cross-platform support", "Easy installation"]
            else:
                features = ["Clean code architecture", "Documentation", "Testing"]
        return features[:5]

    def generate_metadata(self) -> Dict[str, Any]:
        return {
            "repository_name": self.get_repository_name(),
            "description": self.extract_description_from_readme(),
            "topics": self.generate_topics(),
            "created_date": datetime.now().strftime('%Y-%m-%d'),
            "project_type": self.detect_project_type(),
            "primary_language": self.detect_primary_language(),
            "license": self.detect_license(),
            "features": self.extract_features()
        }
