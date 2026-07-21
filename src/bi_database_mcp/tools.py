from typing import Dict, List, Any, Optional
from bi_database_mcp.db_manager import DatabaseManager


class BITools:
    """
    Exposes Business Intelligence database tools for MCP integration.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def list_tables(self) -> List[str]:
        """Lists all table names available in the database."""
        return self.db.list_tables()

    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Inspects column definitions, types, primary keys, and foreign keys for a table."""
        return self.db.describe_table(table_name)

    def execute_query(self, sql_query: str, limit: int = 100) -> Dict[str, Any]:
        """
        Executes a read-only SELECT query against the database.
        Enforces security checks to block mutation commands (INSERT, UPDATE, DELETE, DROP).
        """
        return self.db.execute_query(sql_query, limit=limit)

    def get_database_summary(self) -> Dict[str, Any]:
        """Provides a high-level summary of all tables and row counts."""
        return self.db.get_database_summary()
