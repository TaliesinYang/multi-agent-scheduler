"""
Docker Executor for OS Tasks

Manages Docker containers and executes shell commands for AgentBench OS interaction tasks.
"""

import asyncio
import re
from typing import Optional, Dict, Any
import docker
from docker.models.containers import Container


class DockerExecutor:
    """
    Docker container executor for OS tasks

    Features:
    - Container lifecycle management (create, start, stop, remove)
    - Shell command execution with timeout
    - Output cleaning (removes ANSI escape codes)
    - Container reuse for efficiency

    Example:
        executor = DockerExecutor()
        await executor.start_container("ubuntu:22.04")
        result = await executor.execute_shell("ls -la /root")
        await executor.stop_container()
    """

    def __init__(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker: {e}")

        self.container: Optional[Container] = None
        self.container_id: Optional[str] = None

    async def start_container(
        self,
        image: str = "ubuntu:22.04",
        command: str = "/bin/bash",
        detach: bool = True,
        remove: bool = False,
        **kwargs
    ) -> str:
        """
        Start a Docker container

        Args:
            image: Docker image name (default: ubuntu:22.04)
            command: Command to run (default: /bin/bash)
            detach: Run in background (default: True)
            remove: Auto-remove when stopped (default: False)
            **kwargs: Additional docker.containers.run() parameters

        Returns:
            Container ID
        """
        try:
            # Pull image if not exists
            try:
                self.client.images.get(image)
            except docker.errors.ImageNotFound:
                print(f"Pulling Docker image: {image}")
                self.client.images.pull(image)

            # Create and start container
            self.container = self.client.containers.run(
                image,
                command=command,
                detach=detach,
                remove=remove,
                stdin_open=True,
                tty=True,
                **kwargs
            )

            self.container_id = self.container.id
            return self.container_id

        except Exception as e:
            raise RuntimeError(f"Failed to start container: {e}")

    async def execute_shell(
        self,
        command: str,
        timeout: float = 30.0,
        workdir: Optional[str] = None
    ) -> str:
        """
        Execute shell command in container

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds (default: 30)
            workdir: Working directory (optional)

        Returns:
            Command output (stdout + stderr)

        Raises:
            RuntimeError: If container is not running
            asyncio.TimeoutError: If command times out
        """
        if not self.container:
            raise RuntimeError("Container not started. Call start_container() first.")

        try:
            # Build exec command
            exec_kwargs = {
                "cmd": ["bash", "-c", command],
                "stdout": True,
                "stderr": True,
                "stdin": False
            }

            if workdir:
                exec_kwargs["workdir"] = workdir

            # Execute with timeout
            loop = asyncio.get_event_loop()

            async def run_exec():
                """Run exec in thread pool (docker-py is blocking)"""
                return await loop.run_in_executor(
                    None,
                    lambda: self.container.exec_run(**exec_kwargs)
                )

            # Wait with timeout
            exec_result = await asyncio.wait_for(run_exec(), timeout=timeout)

            # Extract output
            exit_code = exec_result.exit_code
            output = exec_result.output.decode('utf-8', errors='replace')

            # Clean output (remove ANSI escape codes)
            output = self._clean_output(output)

            # Add exit code if non-zero
            if exit_code != 0:
                output += f"\n[Exit code: {exit_code}]"

            return output

        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Command timed out after {timeout}s: {command}")

        except Exception as e:
            raise RuntimeError(f"Failed to execute command: {e}")

    def _clean_output(self, output: str) -> str:
        """
        Clean command output by removing ANSI escape codes

        Args:
            output: Raw command output

        Returns:
            Cleaned output
        """
        # Remove ANSI escape sequences (colors, cursor movement, etc.)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', output)

        # Remove carriage returns
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')

        # Strip trailing whitespace
        cleaned = cleaned.strip()

        return cleaned

    async def stop_container(self, remove: bool = True):
        """
        Stop and optionally remove container

        Args:
            remove: Remove container after stopping (default: True)
        """
        if not self.container:
            return

        try:
            loop = asyncio.get_event_loop()

            # Stop container
            await loop.run_in_executor(None, self.container.stop)

            # Remove if requested
            if remove:
                await loop.run_in_executor(None, self.container.remove)

            self.container = None
            self.container_id = None

        except Exception as e:
            print(f"Warning: Failed to stop container: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get container status

        Returns:
            Dict with container_id, status, image
        """
        if not self.container:
            return {"status": "not_started"}

        try:
            self.container.reload()
            return {
                "container_id": self.container_id,
                "status": self.container.status,
                "image": self.container.image.tags[0] if self.container.image.tags else "unknown"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_container()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop_container()


# Singleton instance for shared use
_default_executor: Optional[DockerExecutor] = None


def get_default_executor() -> DockerExecutor:
    """
    Get or create default Docker executor

    Returns:
        Shared DockerExecutor instance
    """
    global _default_executor
    if _default_executor is None:
        _default_executor = DockerExecutor()
    return _default_executor
