import re
import sqlparse
from typing import Tuple


class UnsafeQueryError(PermissionError):
    """Raised when an SQL query violates read-only safety rules."""
    pass


class SQLGuard:
    """
    Enforces read-only safety policies on SQL queries to prevent unauthorized database modifications.
    """

    FORBIDDEN_KEYWORDS = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "RENAME", "REPLACE", "GRANT", "REVOKE", "ATTACH", "DETACH"
    }

    def __init__(self, allow_multi_statement: bool = False):
        self.allow_multi_statement = allow_multi_statement

    def validate_query(self, sql_query: str) -> str:
        """
        Validates an SQL query string to ensure it is read-only and safe.

        Args:
            sql_query: The SQL query string to validate.

        Returns:
            The sanitized/validated SQL string.

        Raises:
            UnsafeQueryError: If the query contains mutating keywords or multiple statements.
        """
        cleaned_query = sql_query.strip()

        if not cleaned_query:
            raise UnsafeQueryError("Empty query provided.")

        # Check for multiple statements
        statements = sqlparse.parse(cleaned_query)
        if len(statements) > 1 and not self.allow_multi_statement:
            raise UnsafeQueryError("Multi-statement queries are forbidden for security reasons.")

        for statement in statements:
            stmt_type = statement.get_type()
            
            # Check statement type
            if stmt_type not in ("SELECT", "UNKNOWN"):
                # Handle WITH (CTE) queries which sqlparse might tag as UNKNOWN or SELECT
                first_token = str(statement.token_first(skip_ws=True, skip_cm=True)).upper()
                if stmt_type != "SELECT" and first_token not in ("SELECT", "WITH", "EXPLAIN"):
                    raise UnsafeQueryError(
                        f"Statement type '{stmt_type}' ({first_token}) is forbidden. Only SELECT queries are permitted."
                    )

            # Extract all tokens to check for forbidden DDL/DML keywords
            flat_tokens = [
                token.value.upper() for token in statement.flatten()
                if not token.is_whitespace and token.ttype != sqlparse.tokens.Comment
            ]

            for token in flat_tokens:
                if token in self.FORBIDDEN_KEYWORDS:
                    raise UnsafeQueryError(
                        f"Forbidden keyword '{token}' detected in query. Only read-only queries are allowed."
                    )

        return cleaned_query
