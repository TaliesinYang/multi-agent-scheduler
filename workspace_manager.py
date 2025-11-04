"""
Workspace Manager for Multi-Agent System

Manages workspace directories where agents create, modify, and read files.
Supports session-based continuous development with metadata tracking.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class WorkspaceManager:
    """
    Manages workspace directories for multi-agent execution

    Features:
    - Automatic workspace creation with timestamps
    - Metadata tracking for sessions
    - File creation/modification logging
    - Support for both relative and absolute paths

    Example:
        manager = WorkspaceManager()
        workspace = manager.create_workspace("my-app")
        # Agents work in: workspaces/my-app/
    """

    def __init__(self, base_dir: str = "workspaces"):
        """
        Initialize workspace manager

        Args:
            base_dir: Base directory for all workspaces (default: "workspaces")
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_workspace(
        self,
        name: Optional[str] = None,
        use_timestamp: bool = True
    ) -> Path:
        """
        Create a new workspace directory

        Args:
            name: Workspace name (None for auto-generated)
            use_timestamp: Append timestamp to name (default: True)

        Returns:
            Absolute path to created workspace

        Example:
            # Auto-generated: workspaces/20251103_150000/
            ws = manager.create_workspace()

            # Named: workspaces/my-app_20251103_150000/
            ws = manager.create_workspace("my-app")

            # Named without timestamp: workspaces/my-app/
            ws = manager.create_workspace("my-app", use_timestamp=False)
        """
        if name is None:
            # Auto-generate name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workspace_name = timestamp
        else:
            if use_timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                workspace_name = f"{name}_{timestamp}"
            else:
                workspace_name = name

        workspace_path = self.base_dir / workspace_name
        workspace_path.mkdir(parents=True, exist_ok=True)

        return workspace_path.absolute()

    def get_workspace_path(
        self,
        name: str,
        create_if_missing: bool = True
    ) -> Path:
        """
        Get workspace path by name

        Args:
            name: Workspace name or absolute path
            create_if_missing: Create directory if it doesn't exist

        Returns:
            Absolute path to workspace

        Example:
            # Relative name
            ws = manager.get_workspace_path("my-app")
            # Returns: /abs/path/workspaces/my-app

            # Absolute path
            ws = manager.get_workspace_path("/custom/path")
            # Returns: /custom/path
        """
        path = Path(name)

        if path.is_absolute():
            workspace_path = path
        else:
            workspace_path = self.base_dir / name

        if create_if_missing:
            workspace_path.mkdir(parents=True, exist_ok=True)

        return workspace_path.absolute()

    def save_metadata(
        self,
        workspace_path: Path,
        metadata: Dict
    ):
        """
        Save workspace metadata to .workspace_metadata.json

        Args:
            workspace_path: Path to workspace
            metadata: Metadata dictionary to save

        Metadata structure:
            {
                "created_at": "2025-11-03T15:00:00",
                "session_id": "20251103_150000",
                "user_task": "Build a web application",
                "files_created": ["backend/main.py", "frontend/App.jsx"],
                "files_modified": ["README.md"],
                "last_updated": "2025-11-03T15:30:00"
            }
        """
        metadata_file = workspace_path / ".workspace_metadata.json"

        # Add last_updated timestamp
        metadata["last_updated"] = datetime.now().isoformat()

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def load_metadata(
        self,
        workspace_path: Path
    ) -> Optional[Dict]:
        """
        Load workspace metadata from .workspace_metadata.json

        Args:
            workspace_path: Path to workspace

        Returns:
            Metadata dictionary or None if file doesn't exist
        """
        metadata_file = workspace_path / ".workspace_metadata.json"

        if not metadata_file.exists():
            return None

        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_files(
        self,
        workspace_path: Path,
        exclude_hidden: bool = True,
        relative: bool = True
    ) -> List[str]:
        """
        List all files in workspace

        Args:
            workspace_path: Path to workspace
            exclude_hidden: Exclude files starting with '.' (default: True)
            relative: Return paths relative to workspace (default: True)

        Returns:
            List of file paths

        Example:
            files = manager.list_files(workspace_path)
            # Returns: ['backend/main.py', 'frontend/App.jsx', 'README.md']
        """
        files = []

        for item in workspace_path.rglob('*'):
            if item.is_file():
                # Skip hidden files if requested
                if exclude_hidden and item.name.startswith('.'):
                    continue

                if relative:
                    # Get path relative to workspace
                    rel_path = item.relative_to(workspace_path)
                    files.append(str(rel_path))
                else:
                    files.append(str(item))

        return sorted(files)

    def list_workspaces(self) -> List[str]:
        """
        List all existing workspaces

        Returns:
            List of workspace names

        Example:
            workspaces = manager.list_workspaces()
            # Returns: ['my-app_20251103_150000', '20251103_140000']
        """
        if not self.base_dir.exists():
            return []

        workspaces = []
        for item in self.base_dir.iterdir():
            if item.is_dir():
                workspaces.append(item.name)

        return sorted(workspaces)

    def get_workspace_info(self, workspace_path: Path) -> Dict:
        """
        Get comprehensive workspace information

        Args:
            workspace_path: Path to workspace

        Returns:
            Dictionary with workspace info including:
            - path: Absolute path
            - exists: Whether workspace exists
            - files: List of files
            - metadata: Workspace metadata (if available)
            - size: Total size in bytes
        """
        info = {
            "path": str(workspace_path.absolute()),
            "exists": workspace_path.exists(),
            "files": [],
            "metadata": None,
            "size": 0
        }

        if workspace_path.exists():
            info["files"] = self.list_files(workspace_path)
            info["metadata"] = self.load_metadata(workspace_path)

            # Calculate total size
            total_size = 0
            for file_path in workspace_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            info["size"] = total_size

        return info

    def validate_workspace(self, workspace_path: str) -> tuple[bool, str]:
        """
        Validate workspace path for CLI agent compatibility

        Checks for potential issues that may cause CLI tools to fail:
        - Path length (>200 chars may cause issues)
        - Special characters that break shell commands
        - Spaces in path (warning only)
        - Write permissions

        Args:
            workspace_path: Path to validate (string or Path object)

        Returns:
            (is_valid, error_message): Tuple of boolean and error description

        Example:
            >>> manager = WorkspaceManager()
            >>> is_valid, error = manager.validate_workspace("/path/to/workspace")
            >>> if not is_valid:
            ...     print(f"Validation failed: {error}")
        """
        path = Path(workspace_path)
        resolved_path = str(path.resolve())

        # Check 1: Path length (some CLI tools have issues with long paths)
        if len(resolved_path) > 200:
            return False, (
                f"Path too long ({len(resolved_path)} chars, max recommended: 200).\n"
                f"   Consider using a shorter path or creating a symlink:\n"
                f"   ln -s \"{resolved_path}\" ~/mas-workspace"
            )

        # Check 2: Special characters that break shell commands
        dangerous_chars = ['"', "'", '`', '$', '\\']
        found_chars = [c for c in dangerous_chars if c in resolved_path]
        if found_chars:
            return False, (
                f"Path contains shell special characters: {', '.join(found_chars)}\n"
                f"   These characters can cause CLI tools to fail.\n"
                f"   Please use a path without: \" ' ` $ \\"
            )

        # Check 3: Spaces (warning but not blocking)
        if ' ' in resolved_path:
            print(f"⚠️  Warning: Path contains spaces: {resolved_path}")
            print(f"   This may cause issues with some CLI tools.")
            print(f"   Our code uses shlex.quote() for protection, but be aware.")

        # Check 4: Path exists and is a directory
        if path.exists() and not path.is_dir():
            return False, f"Path exists but is not a directory: {resolved_path}"

        # Check 5: Write permissions (if path exists)
        if path.exists():
            if not os.access(path, os.W_OK):
                return False, f"Workspace not writable: {resolved_path}"
        else:
            # Check parent directory is writable
            parent = path.parent
            if not parent.exists():
                return False, f"Parent directory does not exist: {parent}"
            if not os.access(parent, os.W_OK):
                return False, f"Parent directory not writable: {parent}"

        return True, ""
