# 📊 Business Intelligence Database MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Protocol](https://img.shields.io/badge/MCP-1.0.0-green.svg)](https://modelcontextprotocol.io)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)

A safe, production-grade **Model Context Protocol (MCP)** server that exposes database schema discovery and guarded **read-only SQL query execution** tools to Large Language Models (LLMs). Supports **SQLite** out-of-the-box and any **PostgreSQL / MySQL / SQL Server** database via SQLAlchemy.

---

## 📽️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["LLM Host / AI Client"]
        A[Claude Desktop / Cursor / LangChain]
    end

    subgraph MCP ["BI Database MCP Server"]
        B[Stdio Server Transport]
        C[FastMCP Tool Dispatcher]
        D[SQLGuard Security Layer]
        E[SQLAlchemy Database Manager]
    end

    subgraph Database ["Database Storage"]
        F[(Sample SQLite DB)]
        G[(PostgreSQL / Remote DB)]
    end

    A <-->|JSON-RPC via Stdio| B
    B --> C
    C --> D
    D -->|Query Validated SELECT| E
    D -.->|Forbidden DDL/DML Blocked!| X[UnsafeQueryError]
    E --> F
    E --> G
```

---

## 💡 Real-World Use Case

Connecting an LLM directly to corporate database infrastructure provides immense analytical power (automated reporting, natural language data exploration, SQL generation), but exposes critical risks:
* **Accidental Data Loss**: LLMs issuing `DELETE`, `UPDATE`, or `DROP` statements due to hallucinations or prompt injection.
* **Database Overload**: LLMs generating un-paginated queries returning millions of rows.
* **Credential Exposure**: Exposing database connection strings to third-party cloud AI vendors.

### How This Server Protects Your Database
1. **Strict Read-Only Enforcement (`SQLGuard`)**: Parses every incoming SQL query using `sqlparse` and enforces strict `SELECT` query rules. Mutation commands (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`) trigger an instant `UnsafeQueryError`.
2. **Multi-Statement Blocking**: Prevents query stacking attacks (e.g. `SELECT 1; DROP TABLE customers`).
3. **Automated Result Caps**: Automatically appends `LIMIT` clauses to queries missing row bounds to preserve memory.
4. **Instant Seed Dataset**: Ships with a ready-to-query e-commerce sample database (`customers`, `orders`, `products`) so you can test capabilities immediately without setting up external servers.

---

## 🧰 Available MCP Tools

This server exposes **4 tools** over standard I/O (stdio) transport:

### 1. `list_tables`
Lists all tables and views in the connected database.
* **Returns**: JSON object containing list of table names.

### 2. `describe_table`
Returns detailed column definitions, data types, primary keys, and foreign key relationships.
* **Parameters**:
  - `table_name` *(string, required)*: Name of the table to inspect.

### 3. `execute_query`
Safely executes a read-only `SELECT` query against the database.
* **Parameters**:
  - `sql_query` *(string, required)*: Read-only SQL query to run.
  - `limit` *(integer, default: `100`)*: Max row count returned.

### 4. `get_database_summary`
Provides high-level database overview metrics (total table count and row counts per table).

---

## 📦 Installation & Quickstart

### Prerequisites
* Python 3.10 or higher
* Git

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/bi-database-mcp-server.git
cd bi-database-mcp-server

# 2. Create and activate virtual environment
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\activate

# On Linux / macOS:
source venv/bin/activate

# 3. Install package & dependencies
pip install -e .
```

---

## ⚙️ Configuration (Claude Desktop / Cursor)

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:
* **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
* **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

#### Using Built-in Sample SQLite Database:
```json
{
  "mcpServers": {
    "bi-database": {
      "command": "D:/Projects/bi-database-mcp-server/venv/Scripts/python.exe",
      "args": [
        "-m",
        "bi_database_mcp.server"
      ]
    }
  }
}
```

#### Connecting to Custom PostgreSQL / MySQL Database:
```json
{
  "mcpServers": {
    "bi-database": {
      "command": "python",
      "args": ["-m", "bi_database_mcp.server"],
      "env": {
        "DATABASE_URI": "postgresql://user:password@localhost:5432/analytics_db"
      }
    }
  }
}
```

---

## 🧪 Testing & Verification

Run the test suite to verify read-only SQL enforcement, multi-statement blocking, and query execution:

```bash
python -m pytest -o pythonpath=src
```

### Expected Output
```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
collected 4 items

tests\test_database.py ....                                              [100%]

============================== 4 passed in 0.08s ==============================
```

---

## 🤖 Example BI Prompts to Try with Your LLM

1. **Schema Discovery**:
   > *"Summarize the database structure, list all tables, and describe the schema of the `orders` table."*

2. **Sales Analytics**:
   > *"Run a SQL query to calculate the top 3 customers by total spending across all completed orders."*

3. **Inventory Inspection**:
   > *"Find all products in the `Electronics` category that have stock quantity lower than 50 items."*

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
