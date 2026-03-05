import streamlit as st

st.title("Business Metrics Warehouse")

tab_overview, tab_pipeline, tab_models, tab_metrics, tab_insights = st.tabs(
    [
        "Overview",
        "Data Pipeline",
        "Data Models",
        "Metrics & Analysis",
        "Insights",
    ]
)

# --- Overview ---
with tab_overview:
    st.subheader("Problem Statement")
    st.markdown(
        "This project demonstrates how **raw transactional data** can be transformed into a structured "
        "analytics warehouse that supports business metrics such as revenue, repeat purchases, and customer value. "
        "The goal is to show the full path from raw orders and payments to trustworthy business metrics."
    )

    st.subheader("Architecture")
    st.markdown(
        "The system follows a modern analytics pattern:\n\n"
        "- **Raw layer** — CSV extracts for customers, products, orders, order items, and payments\n"
        "- **Staging layer** — cleaned `stg_*` tables with standardized dates, types, and deduplicated records\n"
        "- **Analytics models** — star schema with `fact_orders` at the center and `dim_customers`, `dim_products`, and `dim_date`\n"
        "- **Metrics layer** — reusable SQL models for revenue, average order value, repeat rate, and customer value\n"
        "- **Dashboard** — this Streamlit page, presenting the pipeline, models, metrics, and insights as a guided case study"
    )

    st.subheader("Technology Stack")
    st.markdown(
        "- **SQL** — transformations for staging, star schema, and metrics\n"
        "- **Python** — orchestration and integration with the Streamlit app\n"
        "- **DuckDB or PostgreSQL** — analytical warehouse engine (planned)\n"
        "- **Streamlit** — interactive case study and metrics dashboard"
    )

    st.subheader("Dataset Overview")
    st.markdown(
        "The analytics warehouse is built around a realistic e‑commerce-style dataset (example scale):\n\n"
        "- **Orders:** ~10,000 rows\n"
        "- **Customers:** ~2,000 rows\n"
        "- **Products:** ~120 rows\n"
        "- **Payments:** ~12,000 rows (including retries and refunds)\n\n"
        "In this skeleton, these numbers are illustrative; the implemented pipeline will load and document the actual counts."
    )

# --- Data Pipeline ---
with tab_pipeline:
    st.subheader("Raw Data")
    st.markdown(
        "Raw extracts arrive as CSV files, modeled as tables such as:\n\n"
        "- `customers_raw` — customer profiles with inconsistent casing, mixed date formats, and occasional duplicates\n"
        "- `products_raw` — products with inconsistent price formats and boolean flags\n"
        "- `orders_raw` — orders with mixed `order_status` values, duplicate IDs, and test orders\n"
        "- `order_items_raw` — line items with quantities and unit prices, including potential duplicates\n"
        "- `payments_raw` — payments and refunds with multiple records per order\n\n"
        "These tables intentionally include issues (missing values, duplicates, inconsistent formats) to motivate the staging layer."
    )

    st.subheader("Staging / Cleaned Data")
    st.markdown(
        "The staging layer (`stg_*` tables) applies data cleaning and normalization:\n\n"
        "- `stg_customers` — trimmed names, lowercased emails, parsed `signup_date`, and deduplicated `customer_id`\n"
        "- `stg_products` — numeric `unit_price`, normalized `is_active` flags, deduplicated `product_id`\n"
        "- `stg_orders` — standardized `order_status`, parsed `order_date`, duplicate `order_id` resolution, and test-order flags\n"
        "- `stg_order_items` — numeric `quantity` and `unit_price`, filtered duplicates or clearly invalid rows\n"
        "- `stg_payments` — parsed `payment_date`, numeric `amount`, and normalized `payment_status`\n"
    )

    st.subheader("Transformation Steps")
    st.markdown(
        "Key transformation steps planned for the staging layer:\n\n"
        "- **Duplicate removal** — resolve multiple rows per primary key (e.g., latest record wins for `customer_id` or `order_id`)\n"
        "- **Type conversion** — cast text prices, quantities, and flags into numeric and boolean types\n"
        "- **Date normalization** — standardize mixed date strings into ISO `YYYY-MM-DD` dates\n"
        "- **Missing-value handling** — flag or filter test orders, null customer IDs, and incomplete payment records\n"
        "- **Status normalization** — map variants like `Completed`, `completed`, and `COMPLETE` into a consistent domain\n"
    )

    st.subheader("Example Staging SQL (planned)")
    st.code(
        "-- Example: normalize order status and parse dates for staging\n"
        "CREATE TABLE stg_orders AS\n"
        "SELECT\n"
        "    order_id,\n"
        "    customer_id,\n"
        "    CAST(order_date AS DATE) AS order_date,\n"
        "    LOWER(TRIM(order_status)) AS order_status,\n"
        "    order_channel,\n"
        "    shipping_country,\n"
        "    shipping_city\n"
        "FROM orders_raw\n"
        "WHERE customer_id IS NOT NULL;",
        language="sql",
    )

# --- Data Models ---
with tab_models:
    st.subheader("Schema Overview")
    st.markdown(
        "The analytics warehouse is organized as a **star schema**:\n\n"
        "- **fact_orders** — one row per order with revenue, item count, status, and foreign keys\n"
        "- **dim_customers** — customer attributes (name, email, geography, segment, signup cohort)\n"
        "- **dim_products** — product attributes (name, category, active flag)\n"
        "- **dim_date** — calendar table for grouping by day, month, and year\n\n"
        "`fact_orders` joins to each dimension on simple surrogate keys, mirroring how BI tools query revenue and customer behavior."
    )

    st.subheader("Tables")
    st.markdown(
        "- `dim_customers(customer_id, customer_name, email, country, city, segment, signup_date, signup_month)`\n"
        "- `dim_products(product_id, product_name, category, is_active)`\n"
        "- `dim_date(date, year, month, year_month)`\n"
        "- `fact_orders(order_id, customer_id, product_id, order_date, order_status, order_channel, gross_revenue, net_revenue, item_count)`"
    )

    st.subheader("Example Queries (planned)")
    st.code(
        "-- Revenue by product category\n"
        "SELECT\n"
        "    p.category,\n"
        "    SUM(f.net_revenue) AS revenue\n"
        "FROM fact_orders f\n"
        "JOIN dim_products p ON f.product_id = p.product_id\n"
        "GROUP BY p.category\n"
        "ORDER BY revenue DESC;",
        language="sql",
    )

    st.code(
        "-- Orders and revenue by customer segment\n"
        "SELECT\n"
        "    c.segment,\n"
        "    COUNT(DISTINCT f.order_id) AS orders,\n"
        "    SUM(f.net_revenue) AS revenue\n"
        "FROM fact_orders f\n"
        "JOIN dim_customers c ON f.customer_id = c.customer_id\n"
        "GROUP BY c.segment\n"
        "ORDER BY revenue DESC;",
        language="sql",
    )

# --- Metrics & Analysis ---
with tab_metrics:
    st.subheader("Core Metrics (planned)")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Revenue", "—", help="Sum of net_revenue across completed orders.")
    with m2:
        st.metric("Average Order Value", "—", help="Total revenue divided by number of orders.")
    with m3:
        st.metric("Repeat Purchase Rate", "—", help="Share of customers with more than one completed order.")
    with m4:
        st.metric("Customer Value (LTV)", "—", help="Average revenue per customer over the dataset window.")

    st.subheader("Planned Visualizations")
    st.markdown(
        "- **Revenue by month** (line chart over `dim_date.year_month`)\n"
        "- **Revenue by product category** (bar chart from `fact_orders` × `dim_products`)\n"
        "- **Revenue or orders by customer segment** (bar chart from `fact_orders` × `dim_customers`)\n"
        "- Optional: simple **cohort-style view** by `signup_month` showing orders or revenue over time"
    )

    st.caption(
        "In the full implementation, this tab will query the metrics layer and render live KPIs and charts. "
        "For now, it documents the intended business metrics."
    )

# --- Insights ---
with tab_insights:
    st.subheader("Key Findings (to be derived)")
    st.markdown(
        "- *Replace with insights on revenue growth, seasonality, and stability once metrics are implemented.*\n"
        "- *Highlight which customer segments drive the most revenue and how repeat purchase behavior differs by segment.*\n"
        "- *Summarize top-performing product categories and any long-tail effects.*"
    )

    st.subheader("Business Impact")
    st.markdown(
        "Once populated, this warehouse will support questions like:\n\n"
        "- How is revenue trending over time by channel, segment, and category?\n"
        "- What is the distribution of customer value across cohorts and segments?\n"
        "- Which products and segments should we prioritize for retention and expansion?\n\n"
        "The goal is a **repeatable, documented metrics system** rather than one-off spreadsheets."
    )

    st.subheader("Next Steps")
    st.markdown(
        "- Implement the raw → staging → analytics → metrics pipeline in SQL and Python.\n"
        "- Connect the Streamlit app to the warehouse engine (DuckDB or PostgreSQL).\n"
        "- Add cohort analysis and deeper segmentation once core metrics are stable.\n"
        "- Compare business metrics over time windows to support planning and forecasting."
    )
