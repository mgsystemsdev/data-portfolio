import streamlit as st

st.set_page_config(
    page_title="Data Portfolio",
    layout="wide",
)

# Sidebar nav: container-style section headers for visibility
st.markdown(
    """
    <style>
    /* Section headers in sidebar nav — container look */
    div[data-testid="stSidebarNav"] div:has(+ ul[data-testid="stSidebarNavItems"]) {
        background: rgba(128, 138, 156, 0.12);
        padding: 0.5rem 0.75rem;
        border-radius: 0.375rem;
        margin: 0.75rem 0 0.25rem 0;
        border-left: 3px solid rgba(128, 138, 156, 0.45);
        font-weight: 600;
        font-size: 0.9rem;
    }
    /* Tweak first section header top margin */
    div[data-testid="stSidebarNav"] > div > div > div:has(+ ul[data-testid="stSidebarNavItems"]):first-of-type {
        margin-top: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Shown in nav and home (Inventory & Business Metrics kept in repo but not in nav until complete)
page_turnover = st.Page("pages/1_Operational_Turnover_Intelligence.py", title="Turnover & Make-Ready Intelligence")
page_playground = st.Page("pages/5_Data_Playground.py", title="Analytics Playground")
about = st.Page("pages/4_About_Me.py", title="About")

# Kept in repo; not in navigation: pages/2_Inventory_Flow_Analytics.py, pages/3_Revenue_Subscription_Analytics.py (Business Metrics Warehouse)

# AI & Learning detail pages (Overview + Explain tabs)
page_ai_assistant = st.Page("pages/6_Personal_Task_Goal_Assistant.py", title="Personal Task & Goal Assistant")
page_ai_teacher = st.Page("pages/7_Data_Analytics_Apprenticeship.py", title="Data Analytics Apprenticeship")
page_ai_pract = st.Page("pages/8_Concept_Practice_Engine.py", title="Concept Practice Engine")
page_ai_metacode = st.Page("pages/9_Code_Analytics_Apprenticeship.py", title="Code & Analytics Apprenticeship")


def home():
    st.title("Data Portfolio")

    st.markdown(
        "Welcome to my data portfolio. This application showcases data engineering and analytics projects "
        "using clean pipelines, SQL, and visualization. "
        "The focus is real problems from **apartment operations**, with a full case study on **Turnover & Make-Ready Intelligence**."
    )

    st.markdown("**Use the sidebar** or the buttons below to navigate to each project.")

    st.divider()

    st.subheader("Analytics & Data Engineering")
    st.caption("Pipelines, SQL, and operational intelligence.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Turnover & Make-Ready Intelligence**")
        st.caption("Make-ready coordination, reconciliation, and pipeline design—problem, data, and conclusions from real operations.")
        st.page_link(page_turnover, label="Open project", icon="📊", use_container_width=True)

    with col2:
        st.markdown("**Analytics Playground**")
        st.caption("SQL, pandas, and Streamlit lab: create tables, insert data, run queries. Same foundations behind the turnover case study.")
        st.page_link(page_playground, label="Open project", icon="🔬", use_container_width=True)

    st.divider()
    st.subheader("AI-Powered Applications")
    st.caption(
        "Personal and learning applications: prompt orchestration, event-sourced state, and structured learning flows."
    )

    ai_col1, ai_col2, ai_col3, ai_col4 = st.columns(4)

    with ai_col1:
        st.markdown("**Personal Task & Goal Assistant**")
        st.caption("Event-driven assistant: chat, silent extraction of tasks, goals, and time logs. SQLite + event sourcing.")
        st.page_link(page_ai_assistant, label="Open", icon="💬", use_container_width=True)

    with ai_col2:
        st.markdown("**Data Analytics Apprenticeship**")
        st.caption("Stage-based (S0–S12) learning for Pandas and SQL. Structured progression and method locking.")
        st.page_link(page_ai_teacher, label="Open", icon="🔧", use_container_width=True)

    with ai_col3:
        st.markdown("**Concept Practice Engine**")
        st.caption("Topic and concept drilling with handout mode. Practice one challenge at a time.")
        st.page_link(page_ai_pract, label="Open", icon="🎯", use_container_width=True)

    with ai_col4:
        st.markdown("**Code & Analytics Apprenticeship**")
        st.caption("Topic-based apprenticeship engine for code and analytics. Same stack as the practice engine.")
        st.page_link(page_ai_metacode, label="Open", icon="🔧", use_container_width=True)


home_page = st.Page(home, title="Home", default=True)

pg = st.navigation({
    "": [home_page, about],
    "Analytics & Data Engineering": [page_turnover, page_playground],
    "AI-Powered Applications": [
        page_ai_assistant,
        page_ai_teacher,
        page_ai_pract,
        page_ai_metacode,
    ],
})
pg.run()
