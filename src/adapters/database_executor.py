"""
Database Executor for DB Tasks

Manages database connections and executes SQL queries for AgentBench database tasks.
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
import aiomysql
import aiosqlite


class DatabaseExecutor:
    """
    Database executor supporting MySQL and SQLite

    Features:
    - Async connection pooling (MySQL)
    - Query execution with timeout
    - Result formatting (JSON)
    - Connection reuse for efficiency

    Example:
        # MySQL
        executor = DatabaseExecutor(db_type="mysql", host="localhost", user="root", password="pwd")
        await executor.connect()
        result = await executor.execute_sql("SELECT * FROM users LIMIT 10")
        await executor.close()

        # SQLite
        executor = DatabaseExecutor(db_type="sqlite", database="test.db")
        await executor.connect()
        result = await executor.execute_sql("SELECT * FROM users")
        await executor.close()
    """

    def __init__(
        self,
        db_type: str = "mysql",
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "agentbench",
        **kwargs
    ):
        """
        Initialize database executor

        Args:
            db_type: Database type ("mysql" or "sqlite")
            host: MySQL host (default: localhost)
            port: MySQL port (default: 3306)
            user: MySQL username (default: root)
            password: MySQL password
            database: Database name or SQLite file path
            **kwargs: Additional connection parameters
        """
        self.db_type = db_type.lower()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.kwargs = kwargs

        # Connection pool/connection
        self.pool: Optional[aiomysql.Pool] = None
        self.sqlite_conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """
        Establish database connection

        Raises:
            RuntimeError: If connection fails
        """
        try:
            if self.db_type == "mysql":
                # Create connection pool
                self.pool = await aiomysql.create_pool(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    db=self.database,
                    minsize=1,
                    maxsize=10,
                    **self.kwargs
                )

            elif self.db_type == "sqlite":
                # Create SQLite connection
                self.sqlite_conn = await aiosqlite.connect(self.database)

            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

        except Exception as e:
            raise RuntimeError(f"Failed to connect to database: {e}")

    async def execute_sql(
        self,
        query: str,
        timeout: float = 30.0,
        fetch_limit: int = 1000
    ) -> str:
        """
        Execute SQL query and return results as JSON

        Args:
            query: SQL query to execute
            timeout: Timeout in seconds (default: 30)
            fetch_limit: Maximum rows to fetch (default: 1000)

        Returns:
            JSON string with query results

        Raises:
            RuntimeError: If not connected or query fails
        """
        if self.db_type == "mysql" and not self.pool:
            raise RuntimeError("Not connected. Call connect() first.")
        elif self.db_type == "sqlite" and not self.sqlite_conn:
            raise RuntimeError("Not connected. Call connect() first.")

        try:
            if self.db_type == "mysql":
                return await self._execute_mysql(query, timeout, fetch_limit)
            else:
                return await self._execute_sqlite(query, timeout, fetch_limit)

        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Query timed out after {timeout}s")

        except Exception as e:
            raise RuntimeError(f"Query failed: {e}")

    async def _execute_mysql(
        self,
        query: str,
        timeout: float,
        fetch_limit: int
    ) -> str:
        """Execute MySQL query"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Execute with timeout
                await asyncio.wait_for(
                    cursor.execute(query),
                    timeout=timeout
                )

                # Determine query type
                query_upper = query.strip().upper()

                if query_upper.startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")):
                    # Fetch results for SELECT queries
                    rows = await cursor.fetchmany(fetch_limit)

                    # Convert to list of dicts
                    result = {
                        "rows": rows,
                        "row_count": len(rows),
                        "truncated": len(rows) == fetch_limit
                    }

                else:
                    # For INSERT/UPDATE/DELETE
                    await conn.commit()
                    result = {
                        "affected_rows": cursor.rowcount,
                        "success": True
                    }

                return json.dumps(result, indent=2, default=str)

    async def _execute_sqlite(
        self,
        query: str,
        timeout: float,
        fetch_limit: int
    ) -> str:
        """Execute SQLite query"""
        cursor = await self.sqlite_conn.execute(query)

        # Determine query type
        query_upper = query.strip().upper()

        if query_upper.startswith(("SELECT", "PRAGMA")):
            # Fetch results
            rows = await cursor.fetchmany(fetch_limit)

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Convert to list of dicts
            result_rows = [dict(zip(columns, row)) for row in rows]

            result = {
                "rows": result_rows,
                "row_count": len(result_rows),
                "truncated": len(result_rows) == fetch_limit
            }

        else:
            # For INSERT/UPDATE/DELETE
            await self.sqlite_conn.commit()
            result = {
                "affected_rows": cursor.rowcount,
                "success": True
            }

        return json.dumps(result, indent=2, default=str)

    async def close(self):
        """Close database connection"""
        try:
            if self.pool:
                self.pool.close()
                await self.pool.wait_closed()
                self.pool = None

            if self.sqlite_conn:
                await self.sqlite_conn.close()
                self.sqlite_conn = None

        except Exception as e:
            print(f"Warning: Failed to close database connection: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get connection status

        Returns:
            Dict with db_type, connected status
        """
        connected = False

        if self.db_type == "mysql" and self.pool:
            connected = not self.pool._closed
        elif self.db_type == "sqlite" and self.sqlite_conn:
            connected = True

        return {
            "db_type": self.db_type,
            "database": self.database,
            "connected": connected
        }

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Default executors
_mysql_executor: Optional[DatabaseExecutor] = None
_sqlite_executor: Optional[DatabaseExecutor] = None


def get_mysql_executor(
    host: str = "localhost",
    user: str = "root",
    password: str = "",
    database: str = "agentbench"
) -> DatabaseExecutor:
    """
    Get or create MySQL executor

    Returns:
        Shared MySQL DatabaseExecutor instance
    """
    global _mysql_executor
    if _mysql_executor is None:
        _mysql_executor = DatabaseExecutor(
            db_type="mysql",
            host=host,
            user=user,
            password=password,
            database=database
        )
    return _mysql_executor


def get_sqlite_executor(database: str = "agentbench.db") -> DatabaseExecutor:
    """
    Get or create SQLite executor

    Returns:
        Shared SQLite DatabaseExecutor instance
    """
    global _sqlite_executor
    if _sqlite_executor is None:
        _sqlite_executor = DatabaseExecutor(
            db_type="sqlite",
            database=database
        )
    return _sqlite_executor
