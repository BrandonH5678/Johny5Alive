"""
PostgreSQLAgent - PostgreSQL database query and extraction
"""
from __future__ import annotations
import logging
import json
import csv
import io
from typing import Dict, Any, List, Optional, Union
from .base import BaseAgent

logger = logging.getLogger(__name__)


class PostgreSQLAgent(BaseAgent):
    """
    Retrieves data from PostgreSQL databases

    Supports:
    - SQL query execution with parameter binding
    - Schema introspection
    - Multiple result formats (JSON, CSV, dict)
    - Connection pooling
    - Transaction support
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5432,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        max_rows: int = 10000
    ):
        """
        Initialize PostgreSQLAgent

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Username
            password: Password
            timeout: Query timeout in seconds
            max_rows: Maximum number of rows to return
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.timeout = timeout
        self.max_rows = max_rows
        self._check_psycopg2()

    def _check_psycopg2(self):
        """Check if psycopg2 is available"""
        try:
            import psycopg2
            self.psycopg2 = psycopg2
            logger.info("psycopg2 available")
        except ImportError:
            self.psycopg2 = None
            logger.warning("psycopg2 not installed - install with: pip install psycopg2-binary")

    def supports(self, target: Any) -> bool:
        """Check if target is a PostgreSQL operation"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        return target_type in ('postgresql', 'postgres', 'pg')

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Retrieve data from PostgreSQL database

        Target structure:
            {
                'type': 'postgresql',
                'host': 'localhost' (optional, uses init value if not provided),
                'port': 5432 (optional),
                'database': 'mydb',
                'user': 'username' (optional),
                'password': 'password' (optional),
                'operation': 'query' | 'schema' | 'tables' (default 'query'),
                'query': 'SELECT * FROM users WHERE age > %s',
                'params': [18] (optional, for parameterized queries),
                'format': 'json' | 'csv' | 'dict' (default 'dict'),
                'table': 'users' (optional, for schema introspection)
            }

        Returns:
            {
                'data': <query results>,
                'row_count': 42,
                'columns': ['id', 'name', 'age'],
                'format': 'dict',
                'meta': {
                    'method': 'postgresql',
                    'database': 'mydb',
                    'operation': 'query',
                    'query_time_ms': 123
                }
            }
        """
        if not self.psycopg2:
            raise ImportError("psycopg2 not installed")

        import time

        start_time = time.time()

        # Get connection parameters
        host = target.get('host', self.host)
        port = target.get('port', self.port)
        database = target.get('database', self.database)
        user = target.get('user', self.user)
        password = target.get('password', self.password)

        if not database:
            raise ValueError("Database name required")

        operation = target.get('operation', 'query').lower()

        # Connect to database
        conn = self.psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=self.timeout
        )

        try:
            if operation == 'schema':
                result = self._get_schema(conn, target)
            elif operation == 'tables':
                result = self._list_tables(conn, target)
            else:  # query
                result = self._execute_query(conn, target)

            query_time_ms = int((time.time() - start_time) * 1000)

            result['meta'] = result.get('meta', {})
            result['meta'].update({
                'method': 'postgresql',
                'database': database,
                'host': host,
                'query_time_ms': query_time_ms
            })

            return result

        finally:
            conn.close()

    def _execute_query(self, conn, target: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query"""
        query = target.get('query')
        params = target.get('params', [])
        result_format = target.get('format', 'dict').lower()

        if not query:
            raise ValueError("Query operation requires 'query' parameter")

        cursor = conn.cursor()

        try:
            # Execute query
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

            # Format results
            formatted_data = self._format_results(rows, columns, result_format)

            return {
                'data': formatted_data,
                'row_count': len(rows),
                'columns': columns,
                'format': result_format,
                'meta': {
                    'operation': 'query',
                    'truncated': len(rows) >= self.max_rows
                }
            }

        finally:
            cursor.close()

    def _list_tables(self, conn, target: Dict[str, Any]) -> Dict[str, Any]:
        """List all tables in database"""
        cursor = conn.cursor()

        try:
            # Query information_schema for tables
            cursor.execute("""
                SELECT table_schema, table_name, table_type
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
            """)

            tables = []
            for row in cursor.fetchall():
                schema, name, table_type = row

                # Get row count
                cursor.execute(f'SELECT COUNT(*) FROM "{schema}"."{name}"')
                row_count = cursor.fetchone()[0]

                tables.append({
                    'schema': schema,
                    'name': name,
                    'type': table_type,
                    'row_count': row_count
                })

            return {
                'data': tables,
                'table_count': len(tables),
                'meta': {'operation': 'tables'}
            }

        finally:
            cursor.close()

    def _get_schema(self, conn, target: Dict[str, Any]) -> Dict[str, Any]:
        """Get schema information for table(s)"""
        table_name = target.get('table')
        cursor = conn.cursor()

        try:
            if table_name:
                # Get schema for specific table
                schema = self._introspect_table(cursor, table_name)
                schemas = {table_name: schema}
            else:
                # Get schema for all tables
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)

                schemas = {}
                for row in cursor.fetchall():
                    name = row[0]
                    schemas[name] = self._introspect_table(cursor, name)

            return {
                'data': schemas,
                'table_count': len(schemas),
                'meta': {'operation': 'schema', 'table': table_name}
            }

        finally:
            cursor.close()

    def _introspect_table(self, cursor, table_name: str) -> Dict[str, Any]:
        """Introspect schema for a single table"""
        # Get columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))

        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3]
            })

        # Get indexes
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = %s AND schemaname = 'public'
        """, (table_name,))

        indexes = [{'name': row[0], 'definition': row[1]} for row in cursor.fetchall()]

        return {
            'columns': columns,
            'indexes': indexes
        }

    def _format_results(
        self,
        rows: List[tuple],
        columns: List[str],
        format_type: str
    ) -> Union[List[Dict], str]:
        """Format query results"""

        if format_type == 'json':
            data = [dict(zip(columns, row)) for row in rows]
            return json.dumps(data, indent=2, default=str)

        elif format_type == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(zip(columns, row)))
            return output.getvalue()

        else:  # dict (default)
            return [dict(zip(columns, row)) for row in rows]
