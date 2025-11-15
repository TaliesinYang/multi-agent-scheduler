"""
CLI-based Tool Executor for AgentBench Tasks

Uses local Bash and SQLite instead of Docker/MySQL.
Designed for CLI-only mode without API dependencies.
"""

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional


class CLIToolExecutor:
    """
    CLI-based tool executor for AgentBench tasks

    Executes tools using local system instead of Docker:
    - execute_shell: Uses local bash
    - execute_sql: Uses local SQLite
    - commit_final_answer: Returns result marker

    Example:
        executor = CLIToolExecutor()
        await executor.initialize(db_path="test.db")
        result = await executor.execute_shell("ls -la")
        await executor.close()
    """

    def __init__(self, db_path: str = "agentbench_cli.db"):
        """
        Initialize CLI tool executor

        Args:
            db_path: SQLite database path
        """
        self.db_path = db_path
        self.db_conn: Optional[sqlite3.Connection] = None
        self.initialized = False

    async def initialize(self, setup_db: bool = True):
        """
        Initialize executor

        Args:
            setup_db: Whether to create test database
        """
        if self.initialized:
            return

        # Initialize SQLite connection
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_conn.row_factory = sqlite3.Row  # Return rows as dicts

        # Setup test database if requested
        if setup_db:
            await self._setup_test_database()

        self.initialized = True
        print(f"✓ CLI Tool Executor initialized (DB: {self.db_path})")

    async def _setup_test_database(self):
        """Create test tables with sample data"""
        cursor = self.db_conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT
            )
        """)

        # Insert sample data
        cursor.execute("DELETE FROM users")  # Clear old data
        cursor.executemany(
            "INSERT INTO users (id, name, age, email) VALUES (?, ?, ?, ?)",
            [
                (1, 'Alice', 25, 'alice@example.com'),
                (2, 'Bob', 30, 'bob@example.com'),
                (3, 'Charlie', 22, 'charlie@example.com'),
                (4, 'David', 35, 'david@example.com'),
                (5, 'Eve', 28, 'eve@example.com')
            ]
        )

        self.db_conn.commit()
        print(f"  ✓ Test database ready (5 users)")

    async def execute_shell(self, command: str, timeout: float = 30.0) -> str:
        """
        Execute shell command on local system

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds

        Returns:
            Command output (stdout + stderr)
        """
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return f"Error: Command timed out after {timeout}s"

            # Combine output
            output = stdout.decode('utf-8', errors='replace')
            if stderr:
                error_text = stderr.decode('utf-8', errors='replace')
                if error_text.strip():
                    output += f"\n[stderr]: {error_text}"

            # Add exit code if non-zero
            if process.returncode != 0:
                output += f"\n[Exit code: {process.returncode}]"

            return output.strip() if output.strip() else "[No output]"

        except Exception as e:
            return f"Error executing command: {str(e)}"

    async def execute_sql(
        self,
        query: str,
        timeout: float = 30.0,
        fetch_limit: int = 1000
    ) -> str:
        """
        Execute SQL query on SQLite database

        Args:
            query: SQL query to execute
            timeout: Timeout (not enforced for SQLite)
            fetch_limit: Maximum rows to fetch

        Returns:
            JSON string with query results
        """
        if not self.db_conn:
            return json.dumps({
                "error": "Database not connected",
                "success": False
            })

        try:
            cursor = self.db_conn.cursor()
            cursor.execute(query)

            # Determine query type
            query_upper = query.strip().upper()

            if query_upper.startswith(("SELECT", "PRAGMA")):
                # Fetch results for SELECT queries
                rows = cursor.fetchmany(fetch_limit)

                # Convert to list of dicts
                result_rows = [dict(row) for row in rows]

                result = {
                    "rows": result_rows,
                    "row_count": len(result_rows),
                    "truncated": len(result_rows) == fetch_limit,
                    "success": True
                }

            else:
                # For INSERT/UPDATE/DELETE
                self.db_conn.commit()
                result = {
                    "affected_rows": cursor.rowcount,
                    "success": True
                }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "success": False
            })

    def commit_final_answer(self, answer: str) -> str:
        """
        Mark task as complete with final answer

        Args:
            answer: Final answer to submit

        Returns:
            Special marker string for detection
        """
        return f"FINAL_ANSWER: {answer}"

    async def close(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None
        self.initialized = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


async def demo():
    """Demo CLI tool executor"""
    print("\n" + "="*60)
    print("CLI Tool Executor Demo")
    print("="*60 + "\n")

    async with CLIToolExecutor() as executor:
        # Test shell execution
        print("[1/3] Testing execute_shell...")
        result = await executor.execute_shell("echo 'Hello from CLI!' && ls -la | head -5")
        print(f"  Result: {result[:100]}...\n")

        # Test SQL execution
        print("[2/3] Testing execute_sql...")
        result = await executor.execute_sql("SELECT * FROM users WHERE age > 25")
        print(f"  Result: {result[:200]}...\n")

        # Test final answer
        print("[3/3] Testing commit_final_answer...")
        result = executor.commit_final_answer("Task completed successfully!")
        print(f"  Result: {result}\n")

    print("="*60)
    print("Demo complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo())
