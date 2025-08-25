# MCP Repo Creator — AI-powered GitHub Repository Automation
[![Releases](https://img.shields.io/badge/Releases-Download%20and%20Run-blue?style=for-the-badge&logo=github)](https://github.com/mpstudyportal/mcp-github-repo-creator/releases)

![MCP GitOps illustration](https://images.unsplash.com/photo-1555066931-4365d14bab8c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwxMTc3M3wwfDF8c2VhcmNofDF8fGFpJTIwZGV2ZWxvcG1lbnR8ZW58MHx8fHwxNjI3NjI0Nzky&ixlib=rb-1.2.1&q=80&w=1200)

MCP Repo Creator helps tools and AI clients use the Model Context Protocol to analyze codebases and create new GitHub repositories automatically. It provides repo analysis, topic and metadata management, automated repo setup, and a simple API and CLI for integration with MCP-compatible AI systems.

Badges
- Build / CI: ![Build](https://img.shields.io/badge/build-passing-brightgreen)
- License: ![License](https://img.shields.io/badge/license-MIT-blue)
- Topics: ![Topics](https://img.shields.io/badge/topics-AI%20Integration-lightgrey)

Topics
![ai-integration](https://img.shields.io/badge/topic-ai--integration-blue?style=flat-square) ![automation](https://img.shields.io/badge/topic-automation-blue?style=flat-square) ![cli-tool](https://img.shields.io/badge/topic-cli--tool-blue?style=flat-square) ![git](https://img.shields.io/badge/topic-git-blue?style=flat-square) ![mcp](https://img.shields.io/badge/topic-mcp-blue?style=flat-square) ![python](https://img.shields.io/badge/topic-python-yellow?style=flat-square)

Quick links
- Releases: https://github.com/mpstudyportal/mcp-github-repo-creator/releases  
  Download the release asset (for example mcp-github-repo-creator.tar.gz or a platform binary) from the Releases page and run the file as shown in Quickstart below. If the Releases page is not reachable, check the repository "Releases" section on GitHub.

What this does
- Analyze repository contents to extract high-value metadata: languages, dependency graph, CI config, tests, license.
- Create new GitHub repos with boilerplate files and maintainer metadata.
- Manage topics and labels based on analysis and user config.
- Expose a small MCP-compatible server API for AI clients to request analysis, generate templates, and push repo scaffolds.
- Provide a CLI that mirrors the core API for automation scripts and pipelines.

Why it matters
- Saves time when onboarding projects.
- Standardizes repo metadata and topics.
- Lets model-driven tools trigger repository operations safely and consistently.
- Supports GitHub API and GitHub CLI workflows.

Features
- Repo analysis: language breakdown, file map, dependency snapshot, test and CI detection.
- Metadata generation: README drafts, topics, repository description, license detection and license file generation.
- Automated setup: repo creation, branch protection, issue templates, CODEOWNERS, default labels.
- MCP server: simple JSON endpoints that accept repository context and return actions or generated files.
- CLI tool: run local analysis, preview generated files, create repos from templates, and execute create/push flows.
- Integration hooks: webhooks and MCP client callbacks.

Screenshots and diagrams
![Architecture diagram](https://raw.githubusercontent.com/github/explore/main/topics/microservices/microservices.png)
(Architecture shows a small MCP server receiving model context and issuing GitHub repository creation calls.)

Getting started (Quickstart)
1. Download release asset from Releases:
   - Visit https://github.com/mpstudyportal/mcp-github-repo-creator/releases and download the binary or archive for your platform.
   - The downloaded file needs to be executed. Example (Linux/macOS):
     ```bash
     # Example: replace with the actual asset name you downloaded
     curl -L -o mcp-github-repo-creator.tar.gz "https://github.com/mpstudyportal/mcp-github-repo-creator/releases/download/vX.Y.Z/mcp-github-repo-creator-vX.Y.Z-linux-amd64.tar.gz"
     tar -xzf mcp-github-repo-creator.tar.gz
     chmod +x mcp-github-repo-creator
     ./mcp-github-repo-creator --help
     ```
   - If the direct asset URL is not available, go to the Releases page and pick the right asset for your platform.

2. Install Python CLI (optional)
   ```bash
   python3 -m pip install mcp-github-repo-creator
   mcpgh --help
   ```

3. Run a local MCP server (example)
   ```bash
   ./mcp-github-repo-creator serve --port 8080 --github-token $GITHUB_TOKEN
   ```
   The server exposes endpoints for:
   - POST /analyze — returns repo analysis and metadata
   - POST /generate — returns files for a new repo (README, LICENSE, topics)
   - POST /create — creates a GitHub repository and pushes initial commit

Configuration
- env variables:
  - GITHUB_TOKEN — token with repo and admin:repo_hook scopes.
  - MCP_SERVER_PORT — port to run the MCP server.
- config file (mcp-config.yaml)
  ```yaml
  github_org: my-org
  default_license: MIT
  templates:
    - name: python-package
      path: templates/python-package
  topics_map:
    ai: ai-integration
    cli: cli-tool
  ```

MCP API (short)
- All endpoints accept and return JSON. The server follows simple MCP patterns: it receives model context and returns a JSON response with artifacts and suggested actions.

1) POST /analyze
Input:
```json
{
  "repo_url": "https://github.com/example/repo",
  "path": "."
}
```
Output:
```json
{
  "languages": ["python", "shell"],
  "files": ["setup.py","README.md"],
  "ci_detected": ["github-actions"],
  "metadata": { "recommended_license": "MIT", "topics": ["python","cli-tool"] }
}
```

2) POST /generate
Input:
```json
{
  "metadata": { "name":"my-new-repo", "description":"A sample project" },
  "template": "python-package"
}
```
Output: returns a ZIP or base64 bundle of generated files.

3) POST /create
Input: metadata + generated files + target org
Action: creates the repo on GitHub, applies topics, sets branch protection if requested.

CLI examples
- Analyze a local repo:
  ```bash
  mcpgh analyze ./my-project
  ```
- Generate files locally:
  ```bash
  mcpgh generate --template python-package --out ./out
  ```
- Create a new repo on GitHub:
  ```bash
  mcpgh create --name my-new-repo --org my-org --private
  ```

Integration with GitHub CLI
- The project provides a thin integration wrapper for gh:
  ```bash
  gh auth login
  gh repo create my-org/my-new-repo --private --source=./out --push
  ```

Security and permissions
- The tool uses GitHub token scopes only for the minimal operations required: repo create, repo admin, and hooks if needed.
- Use GitHub Apps or fine-grained PATs when possible.
- The server validates incoming MCP requests. It supports optional HMAC request signing for trusted model clients.

Template system
- Templates live in a simple directory layout:
  templates/
    python-package/
      template.yml
      files/
- Each template contains a parameter map for name, description, license, and topics. The generator performs simple variable substitution.

Common workflows
- Full automated flow triggered by an AI assistant:
  1. Assistant sends a context to MCP server.
  2. Server analyzes context and proposes a template and topics.
  3. Assistant asks for approval; user approves.
  4. Server generates files and creates the repository.
- Manual flow:
  1. Run analysis locally.
  2. Inspect generated files.
  3. Create repo from CLI.

Examples and recipes
- Auto-tag and topic pipeline
  - Use /analyze to get suggested topics.
  - Map suggestions to canonical topics via config.
  - Apply topics on /create.
- Create repo with CI
  - Choose a template that includes GitHub Actions workflows.
  - After creation, server can optionally enable required status checks.

Advanced: MCP client example (pseudo)
- A model client sends a model context with a repository snapshot.
- The MCP server returns a JSON payload with generated files and an array of Git operations.
- The client or server executes the push.

Troubleshooting
- If releases or assets fail to download:
  - Visit the Releases page directly: https://github.com/mpstudyportal/mcp-github-repo-creator/releases
  - If an asset is missing, check the repo Releases section for the correct tag.
- If GitHub API returns permission errors:
  - Check token scopes and whether the token belongs to a user with org access.
- If analysis misses files:
  - Ensure the server has read access to the repository or pass a full archive.

Releases and updating
- Download and run the release asset from the Releases page. The release asset contains a binary or archive. After download, extract and run the binary for the new version.
[![Download Releases](https://img.shields.io/badge/Download%20Releases-%F0%9F%93%AE-blue?style=for-the-badge&logo=github)](https://github.com/mpstudyportal/mcp-github-repo-creator/releases)

Contributing
- Fork the repo.
- Create a branch for your feature or fix.
- Add tests that cover new behavior.
- Open a pull request with a clear description.
- Keep changes small and focused.

License
- MIT License. See LICENSE file for details.

Support
- Open an issue on GitHub if you find a bug or need a feature.
- For release artifacts, check the Releases page: https://github.com/mpstudyportal/mcp-github-repo-creator/releases

Maintainer notes
- Keep templates small and versioned.
- Add an upgrade script for generated repos when templates change.
- Run static checks on generated files to avoid malformed CI configs.

Credits and references
- Model Context Protocol concepts drawn from MCP design patterns.
- Uses GitHub REST/GraphQL API and optional gh CLI for operations.

Security contact
- Report security issues via the repository issues or the security contact listed in the repository metadata.

END OF FILE