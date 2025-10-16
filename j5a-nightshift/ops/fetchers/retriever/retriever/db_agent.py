"""
DBAgent - SQLite database query and extraction with schema introspection
"""
from __future__ import annotations
import sqlite3
import json
import csv
import io
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from .base import BaseAgent

logger = logging.getLogger(__name__)


class DBAgent(BaseAgent):
    """
    Retrieves data from SQLite databases

    Supports:
    - Schema introspection (tables, columns, indexes)
    - SQL query execution with parameter binding
    - Multiple result formats (JSON, CSV, dict)
    - Transaction support
    - Row count and metadata extraction
    """

    def __init__(
        self,
        timeout: int = 30,
        max_rows: int = 10000,
        detect_types: bool = True
    ):
        """
        Initialize DBAgent

        Args:
            timeout: Database operation timeout in seconds
            max_rows: Maximum number of rows to return
            detect_types: Enable SQLite type detection
        """
        self.timeout = timeout
        self.max_rows = max_rows
        self.detect_types = detect_types

    def supports(self, target: Any) -> bool:
        """Check if target is a SQLite database operation"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        return target_type in ('sqlite', 'db', 'database')

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Retrieve data from SQLite database

        Target structure:
            {
                'type': 'sqlite',
                'path': '/path/to/database.db',
                'operation': 'query' | 'schema' | 'tables' (default 'query'),
                'query': 'SELECT * FROM users WHERE age > ?',
                'params': [18] (optional, for parameterized queries),
                'format': 'json' | 'csv' | 'dict' (default 'dict'),
                'table': 'users' (optional, for schema introspection),
                'transaction': True (optional, wrap in transaction)
            }

        Returns:
            {
                'data': <query results>,
                'row_count': 42,
                'columns': ['id', 'name', 'age'],
                'format': 'dict',
                'meta': {
                    'method': 'sqlite',
                    'database': '/path/to/database.db',
                    'operation': 'query',
                    'query_time_ms': 123
                }
            }
        """
        db_path = target.get('path')
        if not db_path:
            raise ValueError("Database target must include 'path'")

        # Validate database file exists
        db_path_obj = Path(db_path)
        if not db_path_obj.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        operation = target.get('operation', 'query').lower()

        if operation == 'schema':
            return self._get_schema(target)
        elif operation == 'tables':
            return self._list_tables(target)
        else:  # query
            return self._execute_query(target)

    def _execute_query(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        import time

        db_path = target['path']
        query = target.get('query')
        params = target.get('params', [])
        result_format = target.get('format', 'dict').lower()
        use_transaction = target.get('transaction', False)

        if not query:
            raise ValueError("Query operation requires 'query' parameter")

        logger.info(f"Executing query on {db_path}: {query[:100]}...")

        start_time = time.time()

        # Connect to database
        detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES if self.detect_types else 0
        conn = sqlite3.connect(
            db_path,
            timeout=self.timeout,
            detect_types=detect_types
        )

        try:
            # Set row factory for dict-like access
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Begin transaction if requested
            if use_transaction:
                cursor.execute("BEGIN TRANSACTION")

            # Execute query with parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Fetch results
            rows = cursor.fetchall()

            # Limit rows
            if len(rows) > self.max_rows:
                logger.warning(f"Limiting results from {len(rows)} to {self.max_rows}")
                rows = rows[:self.max_rows]

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Commit transaction if requested
            if use_transaction:
                conn.commit()

            query_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Query executed: {len(rows)} rows in {query_time_ms}ms")

            # Format results
            formatted_data = self._format_results(rows, columns, result_format)

            return {
                'data': formatted_data,
                'row_count': len(rows),
                'columns': columns,
                'format': result_format,
                'meta': {
                    'method': 'sqlite',
                    'database': db_path,
                    'operation': 'query',
                    'query': query[:200] + '...' if len(query) > 200 else query,
                    'query_time_ms': query_time_ms,
                    'truncated': len(rows) >= self.max_rows
                }
            }

        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            raise ValueError(f"SQLite error: {e}")

        finally:
            conn.close()

    def _list_tables(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """List all tables in database"""
        import time

        db_path = target['path']

        logger.info(f"Listing tables in {db_path}")

        start_time = time.time()

        conn = sqlite3.connect(db_path, timeout=self.timeout)

        try:
            cursor = conn.cursor()

            # Query sqlite_master for all tables
            cursor.execute("""
                SELECT name, type, sql
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                ORDER BY name
            """)

            tables = []
            for row in cursor.fetchall():
                table_name = row[0]
                table_type = row[1]
                table_sql = row[2]

                # Get row count for tables
                row_count = 0
                if table_type == 'table':
                    count_cursor = conn.cursor()
                    count_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = count_cursor.fetchone()[0]

                tables.append({
                    'name': table_name,
                    'type': table_type,
                    'row_count': row_count,
                    'sql': table_sql
                })

            query_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Found {len(tables)} tables/views in {query_time_ms}ms")

            return {
                'data': tables,
                'table_count': len(tables),
                'meta': {
                    'method': 'sqlite',
                    'database': db_path,
                    'operation': 'tables',
                    'query_time_ms': query_time_ms
                }
            }

        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            raise ValueError(f"SQLite error: {e}")

        finally:
            conn.close()

    def _get_schema(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Get schema information for table(s)"""
        import time

        db_path = target['path']
        table_name = target.get('table')  # Optional - if None, get all tables

        logger.info(f"Getting schema for {table_name or 'all tables'} in {db_path}")

        start_time = time.time()

        conn = sqlite3.connect(db_path, timeout=self.timeout)

        try:
            cursor = conn.cursor()

            if table_name:
                # Get schema for specific table
                schema = self._introspect_table(conn, table_name)
                schemas = {table_name: schema}
            else:
                # Get schema for all tables
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type = 'table'
                    ORDER BY name
                """)

                schemas = {}
                for row in cursor.fetchall():
                    name = row[0]
                    schemas[name] = self._introspect_table(conn, name)

            query_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Schema introspection complete in {query_time_ms}ms")

            return {
                'data': schemas,
                'table_count': len(schemas),
                'meta': {
                    'method': 'sqlite',
                    'database': db_path,
                    'operation': 'schema',
                    'table': table_name,
                    'query_time_ms': query_time_ms
                }
            }

        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            raise ValueError(f"SQLite error: {e}")

        finally:
            conn.close()

    def _introspect_table(self, conn: sqlite3.Connection, table_name: str) -> Dict[str, Any]:
        """Introspect schema for a single table"""
        cursor = conn.cursor()

        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'cid': row[0],
                'name': row[1],
                'type': row[2],
                'not_null': bool(row[3]),
                'default_value': row[4],
                'primary_key': bool(row[5])
            })

        # Get indexes
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = []
        for row in cursor.fetchall():
            index_name = row[1]

            # Get index columns
            cursor.execute(f"PRAGMA index_info({index_name})")
            index_columns = [col[2] for col in cursor.fetchall()]

            indexes.append({
                'name': index_name,
                'unique': bool(row[2]),
                'columns': index_columns
            })

        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = []
        for row in cursor.fetchall():
            foreign_keys.append({
                'id': row[0],
                'table': row[2],
                'from_column': row[3],
                'to_column': row[4]
            })

        return {
            'columns': columns,
            'indexes': indexes,
            'foreign_keys': foreign_keys
        }

    def _format_results(
        self,
        rows: List[sqlite3.Row],
        columns: List[str],
        format_type: str
    ) -> Union[List[Dict], str]:
        """Format query results"""

        if format_type == 'json':
            # Convert to list of dicts, then to JSON
            data = [dict(row) for row in rows]
            return json.dumps(data, indent=2, default=str)

        elif format_type == 'csv':
            # Convert to CSV string
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
            return output.getvalue()

        else:  # dict (default)
            # List of dictionaries
            return [dict(row) for row in rows]
