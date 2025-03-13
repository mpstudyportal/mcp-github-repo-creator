#!/usr/bin/env python3
"""
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

setup.py - Setup and VS Code MCP integration for mcp-github-repo-creator

Features:
- Create Python virtualenv and install requirements
- Integrate MCP server into VS Code mcp.json config (safe JSONC merge)
- Backup VS Code mcp.json before changes and maintain a manifest
- Revert functionality to restore configs from backups

Usage:
  python setup.py                # Install + integrate
  python setup.py --revert       # Revert changes using the latest manifest

Options:
  --venv-dir VENV               Path to virtual environment directory (default: ./venv)
  --requirements FILE           Requirements file (default: ./requirements.txt)
  --no-extensions               Skip installing VS Code Copilot extensions
  --dry-run                     Show planned changes without writing
  --manifest FILE               Custom manifest path to use for revert
  --keep-backups                Keep backups after successful revert
  --include-missing             Also create mcp.json for VS Code variants that don't have one yet
  
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import venv as _venv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

VERSION = "1.0.0"


def log(msg: str) -> None:
    print(msg)


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=check)


def ensure_venv(venv_dir: Path) -> Tuple[Path, Path]:
    if not venv_dir.exists():
        log(f"Creating virtual environment at {venv_dir}...")
        builder = _venv.EnvBuilder(with_pip=True)
        builder.create(str(venv_dir))
    else:
        log(f"Virtual environment already exists at {venv_dir}")

    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
        bin_dir = venv_dir / "Scripts"
    else:
        python_exe = venv_dir / "bin" / "python"
        bin_dir = venv_dir / "bin"

    if not python_exe.exists():
        raise RuntimeError(f"Python executable not found in venv: {python_exe}")

    return python_exe, bin_dir


def pip_install(python_exe: Path, args: List[str]) -> None:
    cmd = [str(python_exe), "-m", "pip"] + args
    res = run(cmd, check=False)
    if res.returncode != 0:
        log(res.stdout)
        raise RuntimeError(f"pip command failed: {' '.join(cmd)}")


def detect_mcp_config_candidates() -> List[Path]:
    home = Path.home()
    candidates: List[Path] = []
    if platform.system() == "Darwin":
        candidates += [
            home / "Library/Application Support/Code/User/mcp.json",
            home / "Library/Application Support/Code - Insiders/User/mcp.json",
            home / "Library/Application Support/VSCodium/User/mcp.json",
        ]
    else:
        xdg = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config")))
        candidates += [
            xdg / "Code/User/mcp.json",
            xdg / "Code - Insiders/User/mcp.json",
            xdg / "Code - OSS/User/mcp.json",
            xdg / "VSCodium/User/mcp.json",
            # Flatpak variants
            home / ".var/app/com.visualstudio.code/config/Code/User/mcp.json",
            home / ".var/app/com.visualstudio.code.insiders/config/Code - Insiders/User/mcp.json",
            home / ".var/app/com.visualstudio.code-oss/config/Code - OSS/User/mcp.json",
            home / ".var/app/com.vscodium.codium/config/VSCodium/User/mcp.json",
        ]
    return candidates


def which_all(names: List[str]) -> List[str]:
    out: List[str] = []
    for n in names:
        if shutil.which(n):
            out.append(n)
    return out


def strip_jsonc(text: str) -> str:
    # Remove // line comments
    text = re.sub(r"(^|\s)//.*?$", "", text, flags=re.MULTILINE)
    # Remove /* block comments */
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    # Remove trailing commas in objects/arrays
    text = re.sub(r",\s*(\]|\})", r"\1", text)
    return text


def load_mcp_config(path: Path) -> Tuple[Dict, bool]:
    """Load VS Code MCP config (mcp.json) handling comments.

    Returns (data, ok). If ok is False, the file existed but could not be parsed safely.
    """
    if not path.exists():
        return {"servers": {}, "inputs": []}, True
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return {"servers": {}, "inputs": []}, True
        try:
            return json.loads(strip_jsonc(text)), True
        except Exception:
            # last resort: strict JSON
            return json.loads(text), True
    except Exception as e:
        log(f"Warning: Could not parse MCP config at {path}: {e}")
        return {}, False


def load_settings(path: Path) -> Tuple[Dict, bool]:
    """Load VS Code settings.json handling comments.

    Returns (data, ok). If ok is False, the file existed but could not be parsed safely.
    """
    if not path.exists():
        return {}, True
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return {}, True
        try:
            return json.loads(strip_jsonc(text)), True
        except Exception:
            # last resort: strict JSON
            return json.loads(text), True
    except Exception as e:
        log(f"Warning: Could not parse settings at {path}: {e}")
        return {}, False


def write_mcp_config(path: Path, data: Dict, dry_run: bool = False) -> None:
    """Atomically write mcp.json."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        log(f"[dry-run] Would write {path}")
        return
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def write_settings(path: Path, data: Dict, dry_run: bool = False) -> None:
    """Atomically write settings.json."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        log(f"[dry-run] Would write {path}")
        return
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def backup_settings(path: Path, backups_root: Path, existed_before: bool, dry_run: bool = False) -> Optional[Path]:
    backups_root.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", str(path))
    backup_path = backups_root / f"{safe_name}.{timestamp}.bak"
    if not existed_before:
        # Record intent but no file to copy
        if dry_run:
            log(f"[dry-run] Would record non-existent original for {path}")
        return None
    if dry_run:
        log(f"[dry-run] Would backup {path} -> {backup_path}")
        return backup_path
    shutil.copy2(path, backup_path)
    return backup_path


def merge_for_mcp(data: Dict, repo_dir: Path, venv_python: Path, venv_bin: Path) -> Dict:
    # Ensure servers section exists
    if "servers" not in data:
        data["servers"] = {}
    if "inputs" not in data:
        data["inputs"] = []

    # Add or update the github-repo-creator server
    cfg = {
        "type": "stdio",
        "command": str(venv_python),
        "args": ["server.py"],
        "cwd": str(repo_dir),
        "env": {
            "PATH": f"{venv_bin}{os.pathsep}${{env:PATH}}"
        }
    }
    data["servers"]["github-repo-creator"] = cfg
    return data


def merge_for_mcp_old(data: Dict, repo_dir: Path, venv_python: Path, venv_bin: Path) -> Dict:
    # Ensure Copilot MCP enable flags
    cop = data.get("github.copilot.enable")
    if not isinstance(cop, dict):
        cop = {}
    cop["*"] = True
    cop["mcp"] = True
    data["github.copilot.enable"] = cop

    # Ensure MCP server entry
    servers = data.get("mcp.servers")
    if not isinstance(servers, dict):
        servers = {}

    cfg = {
        "command": str(venv_python),
        "args": ["server.py"],
        "cwd": str(repo_dir),
        "env": {
            "PATH": f"{venv_bin}{os.pathsep}${{env:PATH}}"
        }
    }
    servers["github-repo-creator"] = cfg
    data["mcp.servers"] = servers
    return data


def install_extensions(skip: bool = False) -> None:
    if skip:
        return
    clis = which_all(["code", "code-insiders", "codium", "code-oss"])
    if not clis:
        log("VS Code CLI not found; skipping extension installation.")
        return
    for cli in clis:
        try:
            log(f"Installing Copilot extensions via {cli} (if missing)...")
            run([cli, "--install-extension", "GitHub.copilot"], check=False)
            run([cli, "--install-extension", "GitHub.copilot-chat"], check=False)
        except Exception as e:
            log(f"Warning: Could not install extensions with {cli}: {e}")


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def default_manifest_paths(root: Path) -> Tuple[Path, Path]:
    backups_dir = root / ".mcp-vscode-backups"
    manifest_latest = backups_dir / "manifest-latest.json"
    return backups_dir, manifest_latest


def integrate(args) -> None:
    rroot = repo_root()
    venv_dir = Path(args.venv_dir).resolve()
    req_file = Path(args.requirements).resolve()

    if not req_file.exists():
        log(f"Warning: requirements file not found at {req_file}. Continuing without dependency install.")

    # Create / ensure venv
    venv_python, venv_bin = ensure_venv(venv_dir)

    # Upgrade pip and install deps
    try:
        log("Upgrading pip...")
        pip_install(venv_python, ["install", "--upgrade", "pip"])
    except Exception as e:
        log(f"Warning: pip upgrade failed: {e}")

    if req_file.exists():
        log(f"Installing dependencies from {req_file}...")
        pip_install(venv_python, ["install", "-r", str(req_file)])

    # Optional helper, though script doesn't need it to parse JSONC
    try:
        pip_install(venv_python, ["install", "--upgrade", "json5"])  # best effort
    except Exception:
        pass

    # Integrate with VS Code MCP configuration
    candidates = detect_mcp_config_candidates()
    backups_dir, manifest_latest = default_manifest_paths(rroot)
    manifest_entries = []
    any_updated = False
    for path in candidates:
        parent_exists = path.parent.exists()
        existed_before = path.exists()
        if not existed_before and not args.include_missing:
            # Only modify configs that already exist or have parent directory, to guarantee 1:1 backup->change safety.
            if parent_exists:
                log(f"Creating new MCP config: {path}")
            else:
                log(f"Skipping (no VS Code directory): {path}")
                continue

        # Backup existing file (if present)
        backup_path = backup_settings(path, backups_dir, existed_before, dry_run=args.dry_run)

        # Load, merge, write
        data, ok = load_mcp_config(path)
        if not ok:
            log(f"Skipped unparseable MCP config file without changes: {path}")
            # Record in manifest only if we intended to change it; since we skipped, no write happened
            manifest_entries.append({
                "settings_path": str(path),
                "backup_path": str(backup_path) if backup_path else None,
                "existed_before": existed_before,
                "timestamp": _dt.datetime.now().isoformat(),
                "script_version": VERSION,
                "skipped_unparseable": True,
            })
            continue

        merged = merge_for_mcp(dict(data), rroot, venv_python, venv_bin)
        if merged != data:
            any_updated = True
            write_mcp_config(path, merged, dry_run=args.dry_run)
            log(f"Updated VS Code MCP config: {path}")
        else:
            log(f"No changes needed for: {path}")

        manifest_entries.append({
            "settings_path": str(path),
            "backup_path": str(backup_path) if backup_path else None,
            "existed_before": existed_before,
            "timestamp": _dt.datetime.now().isoformat(),
            "script_version": VERSION,
        })

    if manifest_entries and not args.dry_run:
        backups_dir.mkdir(parents=True, exist_ok=True)
        ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        manifest_path = backups_dir / f"manifest-{ts}.json"
        manifest_path.write_text(json.dumps({"entries": manifest_entries}, indent=2), encoding="utf-8")
        manifest_latest.write_text(json.dumps({"ref": str(manifest_path)}), encoding="utf-8")
        log(f"Saved manifest: {manifest_path}")
        log(f"Updated pointer: {manifest_latest}")

    install_extensions(skip=args.no_extensions)

    if any_updated:
        log("VS Code MCP integration complete. If VS Code is running, please restart it.")
    else:
        log("No VS Code MCP configs were changed. Ensure VS Code is installed and run once to create user directory.")


def resolve_manifest_path(args) -> Optional[Path]:
    if args.manifest:
        p = Path(args.manifest).expanduser().resolve()
        return p if p.exists() else None
    backups_dir, manifest_latest = default_manifest_paths(repo_root())
    if manifest_latest.exists():
        try:
            ref = json.loads(manifest_latest.read_text(encoding="utf-8")).get("ref")
            p = Path(ref)
            if p.exists():
                return p
        except Exception:
            pass
    # Fallback: pick newest manifest-*.json
    if backups_dir.exists():
        manifests = sorted(backups_dir.glob("manifest-*.json"), reverse=True)
        if manifests:
            return manifests[0]
    return None


def revert(args) -> None:
    manifest_path = resolve_manifest_path(args)
    if not manifest_path:
        log("No manifest found to revert. Nothing to do.")
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Failed to read manifest {manifest_path}: {e}")
        return

    entries = manifest.get("entries", [])
    restored = 0
    deleted = 0
    for item in entries:
        settings_path = Path(item.get("settings_path", ""))
        backup_path = Path(item["backup_path"]) if item.get("backup_path") else None
        existed_before = bool(item.get("existed_before"))

        if existed_before:
            if backup_path and backup_path.exists():
                settings_path.parent.mkdir(parents=True, exist_ok=True)
                if args.dry_run:
                    log(f"[dry-run] Would restore {backup_path} -> {settings_path}")
                else:
                    shutil.copy2(backup_path, settings_path)
                restored += 1
            else:
                log(f"Backup missing for {settings_path}; skipping restore.")
        else:
            # The file was created by setup; remove it
            if settings_path.exists():
                if args.dry_run:
                    log(f"[dry-run] Would delete {settings_path}")
                else:
                    try:
                        settings_path.unlink()
                    except Exception:
                        pass
                deleted += 1

    log(f"Revert complete. Restored: {restored}, Deleted new files: {deleted}")

    if not args.keep_backups and not args.dry_run:
        # Cleanup backups and pointer
        backups_dir, manifest_latest = default_manifest_paths(repo_root())
        try:
            if manifest_latest.exists():
                manifest_latest.unlink()
            # Remove all backups (be conservative: only our directory)
            if backups_dir.exists():
                shutil.rmtree(backups_dir)
            log("Removed backups and manifest pointer.")
        except Exception as e:
            log(f"Warning: Failed to clean backups: {e}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Setup MCP GitHub Repository Creator and integrate with VS Code")
    p.add_argument("--venv-dir", default="venv", help="Virtual environment directory")
    p.add_argument("--requirements", default="requirements.txt", help="Requirements file path")
    p.add_argument("--no-extensions", action="store_true", help="Skip installing VS Code Copilot extensions")
    p.add_argument("--dry-run", action="store_true", help="Show planned changes without writing")
    p.add_argument("--manifest", help="Manifest file to use for revert")
    p.add_argument("--keep-backups", action="store_true", help="Keep backups after revert")
    p.add_argument("--revert", action="store_true", help="Revert MCP configs to the backed up versions")
    p.add_argument("--include-missing", action="store_true", help="Also create mcp.json for variants without one")
    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    log(f"MCP GitHub Repo Creator setup v{VERSION}")
    if args.revert:
        revert(args)
        return 0
    integrate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
