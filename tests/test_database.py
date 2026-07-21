import tempfile
import pytest
from bi_database_mcp.security import SQLGuard, UnsafeQueryError
from bi_database_mcp.db_manager import DatabaseManager


def test_sql_guard_valid_queries():
    guard = SQLGuard()
    
    assert guard.validate_query("SELECT * FROM customers") == "SELECT * FROM customers"
    assert guard.validate_query("SELECT c.name, COUNT(o.id) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name")
    assert guard.validate_query("WITH recent_orders AS (SELECT * FROM orders WHERE order_date >= '2024-01-01') SELECT * FROM recent_orders")


def test_sql_guard_blocks_mutations():
    guard = SQLGuard()

    with pytest.raises(UnsafeQueryError):
        guard.validate_query("DELETE FROM customers WHERE id = 1")

    with pytest.raises(UnsafeQueryError):
        guard.validate_query("DROP TABLE orders")

    with pytest.raises(UnsafeQueryError):
        guard.validate_query("UPDATE products SET price_usd = 0")

    with pytest.raises(UnsafeQueryError):
        guard.validate_query("INSERT INTO customers (name) VALUES ('Hacker')")


def test_sql_guard_blocks_multi_statements():
    guard = SQLGuard()

    with pytest.raises(UnsafeQueryError):
        guard.validate_query("SELECT * FROM customers; DROP TABLE customers;")


def test_db_manager_sample_queries():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = f"{tmp_dir}/test_ecommerce.db"
        db_manager = DatabaseManager(db_uri=f"sqlite:///{db_path}")

        try:
            # List tables
            tables = db_manager.list_tables()
            assert "customers" in tables
            assert "products" in tables
            assert "orders" in tables

            # Describe table
            desc = db_manager.describe_table("customers")
            assert desc["table_name"] == "customers"
            col_names = [c["name"] for c in desc["columns"]]
            assert "email" in col_names
            assert "city" in col_names

            # Execute Query
            res = db_manager.execute_query("SELECT * FROM customers WHERE city = 'New York'")
            assert res["row_count"] == 1
            assert res["rows"][0]["name"] == "Alice Smith"

            # Check DB Summary
            summary = db_manager.get_database_summary()
            assert summary["table_count"] == 3
            assert summary["tables"]["customers"]["row_count"] == 5
        finally:
            db_manager.close()
