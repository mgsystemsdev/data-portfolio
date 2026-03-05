"""Data Playground — portfolio page presenting SQL & pandas learning notebooks."""
import streamlit as st

st.title("Data Playground")

tab_overview, tab_sql_setup, tab_create_tables, tab_insert_data, tab_schema, tab_pandas, tab_queries, tab_insights = st.tabs([
    "Overview",
    "SQL Setup",
    "Create Tables",
    "Insert Data",
    "Schema Reference",
    "Pandas Lab",
    "SQL Queries",
    "Insights",
])

# --- Overview ---
with tab_overview:
    st.subheader("Purpose")
    st.markdown(
        "This is my **learning playground** for SQL, pandas, Python, and Streamlit. "
        "I use it to build muscle memory on creating tables, inserting data, and writing queries—"
        "the same foundations that support projects like **Operational Turnover Intelligence**."
    )

    st.subheader("Skills Demonstrated")
    st.markdown(
        "- **SQL** — DDL (CREATE TABLE), DML (INSERT), connection handling, parameterized queries\n"
        "- **Pandas** — Read from SQLite, filter, group, merge; DataFrame creation and transformation\n"
        "- **Python** — sqlite3, context managers (`with`), reusable helper functions"
    )

    st.subheader("What You'll See")
    st.markdown(
        "Below: **SQL Setup** (connection, helper, clean slate), **Create Tables** (all eight table definitions), "
        "**Insert Data** (full seed data for every table), **Schema Reference** (tables and relationships), "
        "**Pandas Lab** (load all tables, Basics, AND/OR, Group/Aggregation, Join/Merge — mirrors the pandas notebook), "
        "**SQL Queries** (same structure: Basics, AND/OR, Group/Aggregation, Join/Merge — mirrors the SQL notebook). "
        "Code is reference only; no execution in the portfolio."
    )

# --- SQL Setup ---
with tab_sql_setup:
    st.subheader("Connection")
    st.markdown("Environment: `sqlite3` and a single database path. Connection is opened with `with sqlite3.connect(DB_PATH) as conn:` so it closes automatically.")
    st.code(
        "import sqlite3\n"
        'DB_PATH = "practice.db"',
        language="python",
    )

    st.subheader("Helper Function")
    st.markdown("Reusable `execute()` with PRAGMA foreign_keys ON; returns fetched rows when `fetch=True`.")
    st.code(
        "def execute(sql, params=None, fetch=False):\n"
        "    with sqlite3.connect(DB_PATH) as conn:\n"
        '        conn.execute("PRAGMA foreign_keys = ON;")\n'
        "        cursor = conn.execute(sql, params or [])\n"
        "        return cursor.fetchall() if fetch else None",
        language="python",
    )

    st.subheader("Clean Slate — Drop Tables")
    st.code(
        'execute("DROP TABLE IF EXISTS order_items")\n'
        'execute("DROP TABLE IF EXISTS payments")\n'
        'execute("DROP TABLE IF EXISTS orders")\n'
        'execute("DROP TABLE IF EXISTS employees")\n'
        'execute("DROP TABLE IF EXISTS departments")\n'
        'execute("DROP TABLE IF EXISTS customers")\n'
        'execute("DROP TABLE IF EXISTS products")\n'
        'execute("DROP TABLE IF EXISTS projects")\n'
        'execute("DROP TABLE IF EXISTS subscriptions")',
        language="python",
    )
    st.markdown("Next: **Create Tables** defines the schema; **Insert Data** loads seed data for all tables.")

# --- Create Tables ---
with tab_create_tables:
    st.markdown("**departments** — Stores department names and office locations. Parent table for employees.")
    st.code(
        'execute("""\n'
        "    CREATE TABLE IF NOT EXISTS departments (\n"
        "        id INTEGER PRIMARY KEY,\n"
        "        department_name TEXT,\n"
        "        location TEXT\n"
        "    )\n"
        '""")',
        language="python",
    )

    st.markdown("**customers** — Stores customer profile information. Parent table for orders.")
    st.code(
        'execute("""\n'
        "    CREATE TABLE IF NOT EXISTS customers (\n"
        "        id INTEGER PRIMARY KEY,\n"
        "        customer_name TEXT,\n"
        "        email TEXT,\n"
        "        city TEXT,\n"
        "        signup_date TEXT\n"
        "    )\n"
        '""")',
        language="python",
    )

    st.markdown("**employees** — Stores employee data and links to departments.")
    st.code(
        'execute("""\n'
        "    CREATE TABLE IF NOT EXISTS employees (\n"
        "        id INTEGER PRIMARY KEY,\n"
        "        name TEXT,\n"
        "        department_id INTEGER,\n"
        "        salary INTEGER,\n"
        "        hire_date TEXT,\n"
        "        FOREIGN KEY (department_id) REFERENCES departments(id)\n"
        "    )\n"
        '""")',
        language="python",
    )

    st.markdown("**products** — Stores product catalog, categories, pricing, and stock levels.")
    st.code(
        'execute("""\n'
        "    CREATE TABLE IF NOT EXISTS products (\n"
        "        id INTEGER PRIMARY KEY,\n"
        "        product_name TEXT,\n"
        "        category TEXT,\n"
        "        price INTEGER,\n"
        "        stock_quantity INTEGER\n"
        "    )\n"
        '""")',
        language="python",
    )

    st.markdown("**orders** — Stores customer orders and links to customers.")
    st.code(
        'execute("""\n'
        "    CREATE TABLE IF NOT EXISTS orders (\n"
        "        id INTEGER PRIMARY KEY,\n"
        "        customer_id INTEGER,\n"
        "        order_date TEXT,\n"
        "        status TEXT,\n"
        "        FOREIGN KEY (customer_id) REFERENCES customers(id)\n"
        "    )\n"
        '""")',
        language="python",
    )

    st.markdown("**order_items** — Bridge table linking orders and products. Each row is one product in one order.")
    st.code(
        'execute("""\n'
        "    CREATE TABLE IF NOT EXISTS order_items (\n"
        "        id INTEGER PRIMARY KEY,\n"
        "        order_id INTEGER,\n"
        "        product_id INTEGER,\n"
        "        quantity INTEGER,\n"
        "        unit_price INTEGER,\n"
        "        FOREIGN KEY (order_id) REFERENCES orders(id),\n"
        "        FOREIGN KEY (product_id) REFERENCES products(id)\n"
        "    )\n"
        '""")',
        language="python",
    )

    st.markdown("**projects** — Standalone table for project timelines and budgets. No foreign keys.")
    st.code(
        'execute("""\n'
        "    CREATE TABLE IF NOT EXISTS projects (\n"
        "        id INTEGER PRIMARY KEY,\n"
        "        project_name TEXT,\n"
        "        start_date TEXT,\n"
        "        end_date TEXT,\n"
        "        budget INTEGER\n"
        "    )\n"
        '""")',
        language="python",
    )

    st.markdown("**payments** — Stores payment records for orders. Links to orders.")
    st.code(
        'execute("""\n'
        "    CREATE TABLE IF NOT EXISTS payments (\n"
        "        id INTEGER PRIMARY KEY,\n"
        "        order_id INTEGER,\n"
        "        payment_date TEXT,\n"
        "        amount INTEGER,\n"
        "        status TEXT,\n"
        "        FOREIGN KEY (order_id) REFERENCES orders(id)\n"
        "    )\n"
        '""")',
        language="python",
    )

# --- Insert Data ---
with tab_insert_data:
    st.markdown("Seed data is inserted with parameterized INSERTs via `executemany()`. Full seed data for every table from the notebook.")
    st.subheader("departments")
    st.code(
        "departments_data = [\n"
        '    ("Engineering", "Building A"),\n'
        '    ("HR", "Building B"),\n'
        '    ("Marketing", "Building A"),\n'
        '    ("Sales", "Building C"),\n'
        '    ("Finance", "Building B"),\n'
        "]\n\n"
        "with sqlite3.connect(DB_PATH) as conn:\n"
        "    conn.executemany(\n"
        '        "INSERT INTO departments (department_name, location) VALUES (?, ?)",\n'
        "        departments_data\n"
        "    )",
        language="python",
    )
    st.subheader("customers")
    st.code(
        "customers_data = [\n"
        '    ("John Smith", "john@email.com", "New York", "2023-01-15"),\n'
        '    ("Maria Garcia", "maria@email.com", "Chicago", "2023-02-20"),\n'
        '    ("David Brown", "david@email.com", "Miami", "2023-03-10"),\n'
        '    ("Sophia Lee", "sophia@email.com", "Los Angeles", "2023-04-05"),\n'
        '    ("Carlos Diaz", "carlos@email.com", "Houston", "2023-05-12"),\n'
        '    ("Emma Wilson", "emma@email.com", "New York", "2023-06-18"),\n'
        '    ("James Taylor", "james@email.com", "Chicago", "2023-07-22"),\n'
        '    ("Olivia Martinez", "olivia@email.com", "Miami", "2024-01-08"),\n'
        '    ("Liam Anderson", "liam@email.com", "Los Angeles", "2024-02-14"),\n'
        '    ("Ava Thomas", "ava@email.com", "Houston", "2024-03-30"),\n'
        "]\n\n"
        "with sqlite3.connect(DB_PATH) as conn:\n"
        "    conn.executemany(\n"
        '        "INSERT INTO customers (customer_name, email, city, signup_date) VALUES (?, ?, ?, ?)",\n'
        "        customers_data\n"
        "    )",
        language="python",
    )
    st.subheader("employees")
    st.code(
        "employees_data = [\n"
        '    ("Alice", 1, 90000, "2021-03-15"),\n'
        '    ("Bob", 1, 85000, "2022-06-01"),\n'
        '    ("Charlie", 2, 60000, "2020-01-10"),\n'
        '    ("David", 2, 65000, "2021-08-20"),\n'
        '    ("Eve", 3, 70000, "2022-02-14"),\n'
        '    ("Frank", 1, 95000, "2019-11-05"),\n'
        '    ("Grace", 3, 72000, "2023-01-08"),\n'
        '    ("Henry", 4, 68000, "2021-05-30"),\n'
        '    ("Isabella", 4, 78000, "2020-09-12"),\n'
        '    ("Jack", 5, 82000, "2022-11-25"),\n'
        "]\n\n"
        "with sqlite3.connect(DB_PATH) as conn:\n"
        "    conn.executemany(\n"
        '        "INSERT INTO employees (name, department_id, salary, hire_date) VALUES (?, ?, ?, ?)",\n'
        "        employees_data\n"
        "    )",
        language="python",
    )
    st.subheader("products")
    st.code(
        "products_data = [\n"
        '    ("Laptop", "Electronics", 1200, 50),\n'
        '    ("Phone", "Electronics", 800, 100),\n'
        '    ("Desk Chair", "Furniture", 250, 40),\n'
        '    ("Notebook", "Office", 5, 500),\n'
        '    ("Monitor", "Electronics", 300, 75),\n'
        '    ("Keyboard", "Electronics", 75, 200),\n'
        '    ("Standing Desk", "Furniture", 450, 30),\n'
        '    ("Printer", "Office", 200, 60),\n'
        '    ("Headphones", "Electronics", 150, 150),\n'
        '    ("Webcam", "Electronics", 80, 120),\n'
        "]\n\n"
        "with sqlite3.connect(DB_PATH) as conn:\n"
        "    conn.executemany(\n"
        '        "INSERT INTO products (product_name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",\n'
        "        products_data\n"
        "    )",
        language="python",
    )
    st.subheader("orders")
    st.code(
        "orders_data = [\n"
        '    (1, "2024-01-15", "completed"),\n'
        '    (2, "2024-01-20", "completed"),\n'
        '    (3, "2024-02-05", "completed"),\n'
        '    (1, "2024-02-14", "completed"),\n'
        '    (4, "2024-03-01", "pending"),\n'
        '    (5, "2024-03-10", "completed"),\n'
        '    (6, "2024-03-15", "cancelled"),\n'
        '    (2, "2024-04-02", "completed"),\n'
        '    (7, "2024-04-18", "completed"),\n'
        '    (3, "2024-05-05", "refunded"),\n'
        '    (8, "2024-05-20", "completed"),\n'
        '    (1, "2024-06-01", "pending"),\n'
        '    (9, "2024-06-15", "completed"),\n'
        '    (10, "2024-07-01", "completed"),\n'
        '    (5, "2024-07-20", "cancelled"),\n'
        "]\n\n"
        "with sqlite3.connect(DB_PATH) as conn:\n"
        "    conn.executemany(\n"
        '        "INSERT INTO orders (customer_id, order_date, status) VALUES (?, ?, ?)",\n'
        "        orders_data\n"
        "    )",
        language="python",
    )
    st.subheader("order_items")
    st.code(
        "order_items_data = [\n"
        "    (1, 1, 1, 1200),\n"
        "    (1, 6, 1, 75),\n"
        "    (2, 2, 1, 800),\n"
        "    (3, 3, 2, 250),\n"
        "    (4, 5, 1, 300),\n"
        "    (4, 9, 2, 150),\n"
        "    (5, 4, 10, 5),\n"
        "    (6, 1, 1, 1200),\n"
        "    (6, 10, 1, 80),\n"
        "    (7, 7, 1, 450),\n"
        "    (8, 2, 1, 800),\n"
        "    (8, 6, 2, 75),\n"
        "    (9, 8, 1, 200),\n"
        "    (10, 3, 1, 250),\n"
        "    (11, 9, 1, 150),\n"
        "    (12, 1, 1, 1200),\n"
        "    (12, 5, 2, 300),\n"
        "    (13, 4, 5, 5),\n"
        "    (14, 10, 3, 80),\n"
        "    (15, 7, 1, 450),\n"
        "]\n\n"
        "with sqlite3.connect(DB_PATH) as conn:\n"
        "    conn.executemany(\n"
        '        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",\n'
        "        order_items_data\n"
        "    )",
        language="python",
    )
    st.subheader("projects")
    st.code(
        "projects_data = [\n"
        '    ("Website Redesign", "2024-01-01", "2024-06-01", 50000),\n'
        '    ("Mobile App", "2024-02-01", "2024-08-01", 75000),\n'
        '    ("Marketing Campaign", "2024-03-01", "2024-05-01", 30000),\n'
        '    ("Automation Tool", "2024-04-01", "2024-09-01", 120000),\n'
        '    ("Data Migration", "2024-05-01", "2024-12-01", 90000),\n'
        '    ("Security Audit", "2024-01-15", "2024-03-15", 25000),\n'
        '    ("API Integration", "2024-06-01", None, 60000),\n'
        '    ("Cloud Migration", "2024-07-01", None, 150000),\n'
        "]\n\n"
        "with sqlite3.connect(DB_PATH) as conn:\n"
        "    conn.executemany(\n"
        '        "INSERT INTO projects (project_name, start_date, end_date, budget) VALUES (?, ?, ?, ?)",\n'
        "        projects_data\n"
        "    )",
        language="python",
    )
    st.subheader("payments")
    st.code(
        "payments_data = [\n"
        '    (1, "2024-01-15", 1275, "paid"),\n'
        '    (2, "2024-01-20", 800, "paid"),\n'
        '    (3, "2024-02-06", 500, "paid"),\n'
        '    (4, "2024-02-14", 450, "paid"),\n'
        '    (5, "2024-03-01", 50, "failed"),\n'
        '    (5, "2024-03-02", 50, "paid"),\n'
        '    (6, "2024-03-15", 1280, "refunded"),\n'
        '    (7, "2024-04-02", 950, "paid"),\n'
        '    (8, "2024-04-18", 800, "paid"),\n'
        '    (9, "2024-04-19", 200, "paid"),\n'
        '    (10, "2024-05-05", 250, "refunded"),\n'
        '    (11, "2024-05-20", 150, "paid"),\n'
        '    (12, "2024-06-01", 1800, "paid"),\n'
        '    (13, "2024-06-15", 25, "paid"),\n'
        '    (14, "2024-07-01", 240, "paid"),\n'
        "]\n\n"
        "with sqlite3.connect(DB_PATH) as conn:\n"
        "    conn.executemany(\n"
        '        "INSERT INTO payments (order_id, payment_date, amount, status) VALUES (?, ?, ?, ?)",\n'
        "        payments_data\n"
        "    )",
        language="python",
    )

# --- Schema Reference ---
with tab_schema:
    st.subheader("Practice schema (practice.db)")
    st.markdown(
        "- **departments** (id, department_name, location) → parent of **employees**\n"
        "- **customers** (id, customer_name, email, city, signup_date) → parent of **orders**\n"
        "- **orders** (id, customer_id, order_date, status) → **order_items** (order_id, product_id, quantity, unit_price) → **products** (id, product_name, category, price, stock_quantity)\n"
        "- **orders** → **payments** (order_id, payment_date, amount, status)\n"
        "- **projects** (id, project_name, start_date, end_date, budget) — standalone"
    )

# --- Pandas Lab ---
with tab_pandas:
    st.subheader("Load all tables")
    st.caption("Load every practice DB table into DataFrames (same as 01_sql_setup).")
    st.code(
        "import sqlite3\n"
        "import pandas as pd\n\n"
        'DB_PATH = "practice.db"\n\n'
        "# Load all practice DB tables (same as 01_sql_setup).\n"
        "with sqlite3.connect(DB_PATH) as conn:\n"
        '    df_departments = pd.read_sql_query("SELECT * FROM departments", conn)\n'
        '    df_employees = pd.read_sql_query("SELECT * FROM employees", conn)\n'
        '    df_customers = pd.read_sql_query("SELECT * FROM customers", conn)\n'
        '    df_orders = pd.read_sql_query("SELECT * FROM orders", conn)\n'
        '    df_products = pd.read_sql_query("SELECT * FROM products", conn)\n'
        '    df_order_items = pd.read_sql_query("SELECT * FROM order_items", conn)\n'
        '    df_projects = pd.read_sql_query("SELECT * FROM projects", conn)\n'
        '    df_payments = pd.read_sql_query("SELECT * FROM payments", conn)',
        language="python",
    )

    st.subheader("Pandas Basics")
    st.caption("Filter rows with a single condition (equivalent to SQL WHERE).")
    st.code(
        'miami_customers = df_customers[df_customers["city"] == "Miami"]\nmiami_customers',
        language="python",
    )
    st.code(
        'df_employees[df_employees["salary"] > 90000]',
        language="python",
    )
    st.code(
        'electronics_products = df_products[df_products["category"] == "Electronics"]\nelectronics_products',
        language="python",
    )
    st.code(
        'completed_orders = df_orders[df_orders["status"] == "completed"]\ncompleted_orders',
        language="python",
    )

    st.subheader("Pandas AND/OR")
    st.caption("Combine conditions with & (AND) and | (OR); use parentheses for clarity.")
    st.code(
        "df_customers[\n"
        '    (df_customers["city"] == "Chicago") &\n'
        '    (df_customers["signup_date"] > "2023-03-01")\n'
        "]",
        language="python",
    )
    st.code(
        "df_customers[\n"
        '    (df_customers["city"] == "Chicago") |\n'
        '    (df_customers["signup_date"] > "2023-03-01")\n'
        "]",
        language="python",
    )
    st.code(
        "high_paid_engineering = df_employees[\n"
        '    (df_employees["department_id"] == 1) &\n'
        '    (df_employees["salary"] > 90000)\n'
        "]\nhigh_paid_engineering",
        language="python",
    )
    st.code(
        "active_orders = df_orders[\n"
        '    (df_orders["status"] == "completed") |\n'
        '    (df_orders["status"] == "pending")\n'
        "]\nactive_orders",
        language="python",
    )
    st.code(
        "expensive_electronics = df_products[\n"
        '    (df_products["category"] == "Electronics") &\n'
        '    (df_products["price"] > 500)\n'
        "]\nexpensive_electronics",
        language="python",
    )

    st.subheader("Pandas Group / Aggregation")
    st.caption("Group by a column and count or sum (equivalent to SQL GROUP BY + aggregate).")
    st.code(
        'employee_counts = df_employees.groupby("department_id")["name"].count()\nemployee_counts',
        language="python",
    )
    st.code(
        'order_status_counts = df_orders.groupby("status")["customer_id"].count()\norder_status_counts',
        language="python",
    )
    st.code(
        "completed_orders = df_orders[df_orders[\"status\"] == \"completed\"]\n"
        "completed_by_customer = (\n"
        "    completed_orders.groupby(\"customer_id\")[\"id\"].count()\n"
        ")\ncompleted_by_customer",
        language="python",
    )

    st.subheader("Pandas Join / Merge")
    st.caption("Merge DataFrames on key columns, then aggregate (equivalent to SQL JOIN + GROUP BY).")
    st.code(
        "merged_df = df_orders.merge(\n"
        "    df_customers,\n"
        "    left_on=\"customer_id\", right_on=\"id\",\n"
        "    suffixes=(\"_order\", \"_customer\")\n"
        ")\n"
        "orders_per_customer = merged_df.groupby(\"customer_name\")[\"id_order\"].count()\n"
        "orders_per_customer",
        language="python",
    )
    st.code(
        "df_order_items[\"line_total\"] = df_order_items[\"quantity\"] * df_order_items[\"unit_price\"]\n"
        "order_totals = df_order_items.groupby(\"order_id\")[\"line_total\"].sum().reset_index()\n"
        "merged_df_1 = order_totals.merge(df_orders, left_on=\"order_id\", right_on=\"id\")\n"
        "merged_2 = merged_df_1.merge(df_customers, left_on=\"customer_id\", right_on=\"id\")\n"
        "revenue_per_customer = merged_2.groupby(\"customer_name\")[\"line_total\"].sum().sort_values(ascending=False)\n"
        "revenue_per_customer",
        language="python",
    )

# --- SQL Queries ---
with tab_queries:
    st.subheader("SQL Basics")
    st.caption("Filter rows with a single condition (SELECT + WHERE).")
    st.code(
        "rows = execute(\"\"\"\n"
        "    SELECT customer_name, city\n"
        "    FROM customers\n"
        "    WHERE city = 'Miami'\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.code(
        "rows = execute(\"\"\"\n"
        "    SELECT name, salary\n"
        "    FROM employees\n"
        "    WHERE salary > 90000\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.code(
        "rows = execute(\"\"\"\n"
        "    SELECT product_name, category, price\n"
        "    FROM products\n"
        "    WHERE category = 'Electronics'\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.code(
        "rows = execute(\"\"\"\n"
        "    SELECT id, customer_id, order_date, status\n"
        "    FROM orders\n"
        "    WHERE status = 'completed'\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )

    st.subheader("SQL AND/OR")
    st.caption("Combine conditions with AND and OR in the WHERE clause.")
    st.code(
        "rows = execute(\"\"\"\n"
        "    SELECT customer_name, city, signup_date\n"
        "    FROM customers\n"
        "    WHERE city = 'Chicago' AND signup_date > '2023-03-01'\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.code(
        "rows = execute(\"\"\"\n"
        "    SELECT customer_name, city, signup_date\n"
        "    FROM customers\n"
        "    WHERE city = 'Chicago' OR signup_date > '2023-03-01'\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.code(
        "rows = execute(\"\"\"\n"
        "    SELECT name, salary, department_id\n"
        "    FROM employees\n"
        "    WHERE department_id = 1 AND salary > 90000\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.code(
        "rows = execute(\"\"\"\n"
        "    SELECT order_date, status\n"
        "    FROM orders\n"
        "    WHERE status = 'completed' OR status = 'pending'\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.code(
        "rows = execute(\"\"\"\n"
        "    SELECT product_name, category, price\n"
        "    FROM products\n"
        "    WHERE category = 'Electronics' AND price > 500\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )

    st.subheader("SQL Group / Aggregation")
    st.caption("Group by a column and aggregate with COUNT/SUM (GROUP BY).")
    st.code(
        "rows = execute(\"\"\"\n"
        "SELECT department_id, COUNT(*)\n"
        "FROM employees\n"
        "GROUP BY department_id\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.code(
        "rows = execute(\"\"\"\n"
        "SELECT status, COUNT(customer_id)\n"
        "FROM orders\n"
        "GROUP BY status\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.code(
        "rows = execute(\"\"\"\n"
        "SELECT customer_id, COUNT(id)\n"
        "FROM orders\n"
        "WHERE status = 'completed'\n"
        "GROUP BY customer_id\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )

    st.subheader("SQL Join / Merge")
    st.caption("JOIN tables on key columns, then aggregate (orders per customer).")
    st.code(
        "rows = execute(\"\"\"\n"
        "SELECT c.customer_name, COUNT(o.id) AS order_count\n"
        "FROM orders o\n"
        "INNER JOIN customers c ON o.customer_id = c.id\n"
        "GROUP BY c.customer_name\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )
    st.caption("Revenue per customer: JOIN order_items → orders → customers, SUM(quantity * unit_price).")
    st.code(
        "rows = execute(\"\"\"\n"
        "SELECT c.customer_name, SUM(oi.quantity * oi.unit_price) AS revenue\n"
        "FROM order_items oi\n"
        "INNER JOIN orders o ON oi.order_id = o.id\n"
        "INNER JOIN customers c ON o.customer_id = c.id\n"
        "GROUP BY c.customer_name\n"
        "ORDER BY revenue DESC\n"
        '""", fetch=True) or []\n\n'
        "for row in rows:\n"
        "    print(row)",
        language="python",
    )

# --- Insights ---
with tab_insights:
    st.subheader("Takeaway")
    st.markdown(
        "This playground reinforces **connection lifecycle** (open, execute, close), **parameterized SQL** for safety, "
        "**clear schema design** (tables and foreign keys), and the **SQL–pandas loop** (read from DB, analyze in DataFrames). "
        "These patterns carry over to the Operational Turnover Intelligence pipeline and to any analytics project."
    )
