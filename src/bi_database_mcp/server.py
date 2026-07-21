import os
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP
from bi_database_mcp.db_manager import DatabaseManager
from bi_database_mcp.tools import BITools

# Allow configuring target DB URI via environment variable
DATABASE_URI = os.environ.get("DATABASE_URI", None)

db_manager = DatabaseManager(db_uri=DATABASE_URI)
bi_tools = BITools(db_manager)

mcp = FastMCP("Business Intelligence Database Server")


@mcp.tool()
def list_tables() -> str:
    """
    Lists all available database tables and views.
    """
    tables = bi_tools.list_tables()
    return json.dumps({"tables": tables}, indent=2)


@mcp.tool()
def describe_table(table_name: str) -> str:
    """
    Returns column names, data types, primary keys, and foreign keys for a specific table.
    """
    schema_info = bi_tools.describe_table(table_name)
    return json.dumps(schema_info, indent=2)


@mcp.tool()
def execute_query(sql_query: str, limit: int = 100) -> str:
    """
    Safely executes a read-only SELECT query against the database.
    Mutating statements (INSERT, UPDATE, DELETE, DROP, ALTER) are strictly forbidden and blocked.
    """
    results = bi_tools.execute_query(sql_query, limit=limit)
    return json.dumps(results, indent=2, default=str)


@mcp.tool()
def get_database_summary() -> str:
    """
    Returns a high-level summary of database table counts and row statistics.
    """
    summary = bi_tools.get_database_summary()
    return json.dumps(summary, indent=2)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
