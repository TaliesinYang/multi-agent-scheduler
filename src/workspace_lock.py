"""
Workspace File Lock and Sandboxed Workspace Manager

Provides file locking for concurrent workspace access and sandboxing for security.
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, Optional, Set
from contextlib import asynccontextmanager


class FileLock:
    """
    Async file lock for preventing concurrent writes

    Example:
        >>> lock = FileLock()
        >>> async with lock.acquire('file.txt'):
        >>>     # Write to file safely
        >>>     pass
    """

    def __init__(self):
        """Initialize file lock manager"""
        self.locks: Dict[str, asyncio.Lock] = {}

    @asynccontextmanager
    async def acquire(self, file_path: str):
        """
        Acquire lock for file

        Args:
            file_path: Path to lock

        Example:
            >>> async with lock.acquire('/path/to/file.txt'):
            >>>     with open('/path/to/file.txt', 'w') as f:
            >>>         f.write('content')
        """
        # Normalize path
        file_path = str(Path(file_path).resolve())

        # Get or create lock
        if file_path not in self.locks:
            self.locks[file_path] = asyncio.Lock()

        lock = self.locks[file_path]

        # Acquire lock
        await lock.acquire()
        try:
            yield lock
        finally:
            lock.release()

    def is_locked(self, file_path: str) -> bool:
        """
        Check if file is locked

        Args:
            file_path: Path to check

        Returns:
            True if locked
        """
        file_path = str(Path(file_path).resolve())
        if file_path not in self.locks:
            return False
        return self.locks[file_path].locked()


class SandboxedWorkspaceManager:
    """
    Sandboxed workspace manager with security restrictions

    Features:
    - Path validation
    - File locking
    - Access control
    - Quota management

    Example:
        >>> manager = SandboxedWorkspaceManager('/workspaces')
        >>> workspace = await manager.create_workspace('project1')
        >>> await manager.write_file(workspace / 'file.txt', 'content')
    """

    def __init__(
        self,
        base_dir: str = "workspaces",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        max_total_size: int = 100 * 1024 * 1024  # 100MB
    ):
        """
        Initialize sandboxed workspace manager

        Args:
            base_dir: Base directory for workspaces
            max_file_size: Maximum single file size in bytes
            max_total_size: Maximum total workspace size in bytes
        """
        self.base_dir = Path(base_dir).resolve()
        self.max_file_size = max_file_size
        self.max_total_size = max_total_size
        self.file_lock = FileLock()

        # Allowed paths (only within base_dir)
        self.allowed_paths: Set[Path] = {self.base_dir}

        # Create base directory
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: Path) -> None:
        """
        Validate path is within sandbox

        Args:
            path: Path to validate

        Raises:
            PermissionError: If path is outside sandbox
        """
        resolved = path.resolve()

        # Check if path is within base_dir
        try:
            resolved.relative_to(self.base_dir)
        except ValueError:
            raise PermissionError(
                f"Access denied: Path {path} is outside sandbox {self.base_dir}"
            )

        # Check for sensitive paths
        sensitive_patterns = ['/etc', '/sys', '/proc', '/dev', '/root', '~']
        path_str = str(resolved)
        for pattern in sensitive_patterns:
            if pattern in path_str:
                raise PermissionError(
                    f"Access denied: Cannot access sensitive path containing '{pattern}'"
                )

    def _check_file_size(self, file_path: Path, content: str) -> None:
        """
        Check if file size is within limits

        Args:
            file_path: Path to file
            content: Content to write

        Raises:
            ValueError: If size exceeds limits
        """
        content_size = len(content.encode('utf-8'))

        if content_size > self.max_file_size:
            raise ValueError(
                f"File too large: {content_size} bytes "
                f"(max: {self.max_file_size} bytes)"
            )

    def _check_workspace_size(self, workspace: Path) -> None:
        """
        Check if workspace size is within limits

        Args:
            workspace: Workspace directory

        Raises:
            ValueError: If size exceeds limits
        """
        total_size = 0
        for file in workspace.rglob('*'):
            if file.is_file():
                total_size += file.stat().st_size

        if total_size > self.max_total_size:
            raise ValueError(
                f"Workspace too large: {total_size} bytes "
                f"(max: {self.max_total_size} bytes)"
            )

    async def create_workspace(
        self,
        name: str,
        use_timestamp: bool = False
    ) -> Path:
        """
        Create sandboxed workspace

        Args:
            name: Workspace name
            use_timestamp: Append timestamp to name

        Returns:
            Workspace path

        Raises:
            PermissionError: If invalid name
        """
        # Validate name
        if '..' in name or '/' in name or '\\' in name:
            raise PermissionError(f"Invalid workspace name: {name}")

        # Create workspace directory
        if use_timestamp:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workspace_name = f"{name}_{timestamp}"
        else:
            workspace_name = name

        workspace_path = self.base_dir / workspace_name
        self._validate_path(workspace_path)

        workspace_path.mkdir(parents=True, exist_ok=True)
        self.allowed_paths.add(workspace_path)

        return workspace_path

    async def write_file(
        self,
        file_path: Path,
        content: str
    ) -> None:
        """
        Write file with locking and validation

        Args:
            file_path: Path to file
            content: Content to write

        Raises:
            PermissionError: If path is invalid
            ValueError: If size exceeds limits
        """
        file_path = Path(file_path)
        self._validate_path(file_path)
        self._check_file_size(file_path, content)

        # Create parent directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with lock
        async with self.file_lock.acquire(str(file_path)):
            file_path.write_text(content, encoding='utf-8')

        # Check workspace size
        workspace = self._get_workspace_for_file(file_path)
        if workspace:
            self._check_workspace_size(workspace)

    async def read_file(self, file_path: Path) -> str:
        """
        Read file with validation

        Args:
            file_path: Path to file

        Returns:
            File content

        Raises:
            PermissionError: If path is invalid
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        self._validate_path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read with lock
        async with self.file_lock.acquire(str(file_path)):
            return file_path.read_text(encoding='utf-8')

    async def delete_file(self, file_path: Path) -> None:
        """
        Delete file with validation

        Args:
            file_path: Path to file

        Raises:
            PermissionError: If path is invalid
        """
        file_path = Path(file_path)
        self._validate_path(file_path)

        if file_path.exists():
            async with self.file_lock.acquire(str(file_path)):
                file_path.unlink()

    def _get_workspace_for_file(self, file_path: Path) -> Optional[Path]:
        """
        Get workspace directory for file

        Args:
            file_path: Path to file

        Returns:
            Workspace path or None
        """
        for workspace in self.allowed_paths:
            try:
                file_path.relative_to(workspace)
                return workspace
            except ValueError:
                continue
        return None

    def get_workspace_info(self, workspace: Path) -> Dict[str, any]:
        """
        Get workspace information

        Args:
            workspace: Workspace path

        Returns:
            Dictionary with workspace info
        """
        self._validate_path(workspace)

        total_size = 0
        file_count = 0

        for file in workspace.rglob('*'):
            if file.is_file():
                total_size += file.stat().st_size
                file_count += 1

        return {
            'path': str(workspace),
            'file_count': file_count,
            'total_size': total_size,
            'size_limit': self.max_total_size,
            'usage_percent': (total_size / self.max_total_size * 100) if self.max_total_size > 0 else 0
        }


# Example usage
if __name__ == "__main__":
    async def test():
        manager = SandboxedWorkspaceManager()

        # Create workspace
        workspace = await manager.create_workspace('test_project')
        print(f"Created workspace: {workspace}")

        # Write file
        test_file = workspace / 'test.txt'
        await manager.write_file(test_file, 'Hello, world!')

        # Read file
        content = await manager.read_file(test_file)
        print(f"File content: {content}")

        # Get info
        info = manager.get_workspace_info(workspace)
        print(f"Workspace info: {info}")

    asyncio.run(test())
