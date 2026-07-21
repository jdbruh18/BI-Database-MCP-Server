import os
import sqlite3
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, inspect, text, Engine
from bi_database_mcp.security import SQLGuard, UnsafeQueryError


class DatabaseManager:
    """
    Manages database connection lifecycle, schema inspection, and guarded SQL execution.
    """

    def __init__(self, db_uri: Optional[str] = None, guard: Optional[SQLGuard] = None):
        self.guard = guard or SQLGuard()
        
        if not db_uri:
            db_path = os.path.abspath("sample_ecommerce.db")
            db_uri = f"sqlite:///{db_path}"

        self.db_uri = db_uri
        
        # If it's a sqlite file URI, ensure sample tables if file doesn't exist or is empty
        if db_uri.startswith("sqlite:///"):
            raw_path = db_uri.replace("sqlite:///", "")
            if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
                self._seed_sample_db(raw_path)

        self.engine: Engine = create_engine(self.db_uri)

    def close(self):
        """Closes all database connections and disposes engine."""
        if hasattr(self, "engine"):
            self.engine.dispose()

    def _seed_sample_db(self, db_path: str):
        """Creates a sample SQLite e-commerce dataset for instant testing."""
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create Tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            city TEXT NOT NULL,
            signup_date DATE NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price_usd REAL NOT NULL,
            stock_quantity INTEGER NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            order_date DATE NOT NULL,
            quantity INTEGER NOT NULL,
            total_amount_usd REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        """)

        # Insert Seed Data
        cursor.executemany("""
        INSERT INTO customers (name, email, city, signup_date) VALUES (?, ?, ?, ?);
        """, [
            ("Alice Smith", "alice@example.com", "New York", "2024-01-15"),
            ("Bob Jones", "bob@example.com", "San Francisco", "2024-02-01"),
            ("Charlie Brown", "charlie@example.com", "Chicago", "2024-02-10"),
            ("Diana Prince", "diana@example.com", "Austin", "2024-03-05"),
            ("Evan Wright", "evan@example.com", "Seattle", "2024-03-20"),
        ])

        cursor.executemany("""
        INSERT INTO products (name, category, price_usd, stock_quantity) VALUES (?, ?, ?, ?);
        """, [
            ("UltraBook Pro 15", "Electronics", 1299.99, 45),
            ("Wireless Noise-Canceling Headphones", "Electronics", 249.50, 120),
            ("Ergonomic Mesh Office Chair", "Furniture", 349.00, 30),
            ("Standing Desk 60x30", "Furniture", 599.99, 15),
            ("Mechanical RGB Keyboard", "Accessories", 119.99, 80),
        ])

        cursor.executemany("""
        INSERT INTO orders (customer_id, product_id, order_date, quantity, total_amount_usd, status) VALUES (?, ?, ?, ?, ?, ?);
        """, [
            (1, 1, "2024-04-01", 1, 1299.99, "Completed"),
            (1, 5, "2024-04-01", 2, 239.98, "Completed"),
            (2, 2, "2024-04-03", 1, 249.50, "Completed"),
            (3, 3, "2024-04-05", 1, 349.00, "Shipped"),
            (4, 4, "2024-04-10", 1, 599.99, "Processing"),
            (5, 2, "2024-04-12", 2, 499.00, "Completed"),
        ])

        conn.commit()
        conn.close()

    def list_tables(self) -> List[str]:
        """Lists all table names in the database."""
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Returns metadata for columns, primary keys, and foreign keys of a table."""
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        if table_name not in tables:
            raise ValueError(f"Table '{table_name}' does not exist in database.")

        columns = [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default", "")) if col.get("default") else None,
            }
            for col in inspector.get_columns(table_name)
        ]

        pk_constraint = inspector.get_pk_constraint(table_name)
        fk_constraints = [
            {
                "constrained_columns": fk["constrained_columns"],
                "referred_table": fk["referred_table"],
                "referred_columns": fk["referred_columns"],
            }
            for fk in inspector.get_foreign_keys(table_name)
        ]

        return {
            "table_name": table_name,
            "columns": columns,
            "primary_key": pk_constraint.get("constrained_columns", []),
            "foreign_keys": fk_constraints,
        }

    def execute_query(self, sql_query: str, limit: int = 100) -> Dict[str, Any]:
        """
        Validates and executes a read-only SELECT query.
        """
        validated_sql = self.guard.validate_query(sql_query)

        # Enforce max limit cap if not present
        if "LIMIT" not in validated_sql.upper():
            validated_sql = f"{validated_sql} LIMIT {limit}"

        with self.engine.connect() as connection:
            result = connection.execute(text(validated_sql))
            keys = list(result.keys())
            rows = [dict(zip(keys, row)) for row in result.fetchall()]

            return {
                "columns": keys,
                "row_count": len(rows),
                "rows": rows,
            }

    def get_database_summary(self) -> Dict[str, Any]:
        """Provides high-level database stats."""
        tables = self.list_tables()
        summary = {"table_count": len(tables), "tables": {}}

        with self.engine.connect() as connection:
            for table in tables:
                count_res = connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                summary["tables"][table] = {"row_count": count_res}

        return summary
