# Optional per-topic metadata (e.g. enforcement layer for prompts). Load dynamically in prompts.
TOPIC_METADATA = {
    "Python": {"enforcement_layer": "python_mastery"},
    "Python: stdlib": {"enforcement_layer": "python_mastery"},
}


def get_enforcement_layer(topic: str) -> str:
    """Return enforcement_layer for topic (e.g. 'python_mastery') or empty string."""
    if not topic or topic == "None":
        return ""
    meta = TOPIC_METADATA.get(topic, {})
    return meta.get("enforcement_layer", "")


TOPIC_MENU = {
    # ━━ PYTHON CORE ━━
    "Python": ["Variables", "Functions", "Loops", "Conditionals", "Classes",
               "Data Structures", "Error Handling", "Modules", "Decorators", "Comprehensions",
               "Generators", "Context Managers", "Type Hints", "Lambda", "Unpacking"],
    "Python: stdlib": [
        "os", "sys", "pathlib", "datetime", "time", "json", "csv", "re",
        "logging", "argparse", "collections", "itertools", "functools",
        "typing", "dataclasses", "math", "random", "subprocess", "shutil",
        "contextlib", "sqlite3", "unittest", "traceback", "warnings",
        "tempfile", "pprint", "inspect", "importlib"],
    # ━━ FRONTEND ━━
    "HTML": ["Structure", "Semantics", "Forms", "Tables", "Media", "Accessibility"],
    "CSS": ["Selectors", "Box Model", "Flexbox", "Grid", "Responsive", "Animations"],
    "JavaScript": ["Variables", "Functions", "Arrays", "Objects", "DOM",
                   "Async", "Promises", "Arrow Functions", "Destructuring", "Modules"],
    "TypeScript": ["Types", "Interfaces", "Generics", "Enums", "Type Guards",
                   "Utility Types", "Declaration Files", "Narrowing"],
    "React": ["Components", "Hooks", "State", "Props", "Routing",
              "Context", "Effects", "Custom Hooks", "Performance"],
    # ━━ BACKEND & APIs ━━
    "FastAPI": ["Routes", "Request Models", "Response Models", "Dependencies",
                "Authentication", "Database Integration", "Middleware", "Error Handling"],
    "Django": ["Models", "Views", "Templates", "URLs", "Forms",
               "Admin", "ORM Queries", "Middleware", "Authentication", "Migrations"],
    "Flask": ["Routes", "Templates", "Blueprints", "Request Handling", "Extensions"],
    "REST API Design": ["Methods", "Status Codes", "Versioning", "Pagination",
                        "Authentication", "Rate Limiting", "Error Responses"],
    "GraphQL": ["Queries", "Mutations", "Schemas", "Resolvers", "Subscriptions"],
    # ━━ DATABASES ━━
    "SQL": ["Core SQL", "Joins", "Aggregations", "Window Functions", "CTEs", "Subqueries", "DDL"],
    "PostgreSQL": ["Data Types", "Indexes", "Transactions", "JSON", "Full Text Search",
                   "Performance", "Views", "Triggers"],
    "SQLite": ["Connection", "Cursors", "CRUD", "Transactions", "Schema", "Parameterized Queries"],
    "SQLAlchemy": ["Engine", "Models", "Queries", "Relationships", "Migrations", "Sessions"],
    "DuckDB": ["Queries", "Aggregations", "Joins", "Window Functions", "Python Integration"],
    "MongoDB": ["Documents", "Queries", "Aggregation", "Indexes", "Schema Design", "Updates"],
    "Redis": ["Keys", "Strings", "Hashes", "Lists", "Sets", "Pub/Sub", "Caching Patterns"],
    # ━━ DATA & ANALYSIS ━━
    "Pandas": ["DataFrame Basics", "Selection", "Cleaning", "Aggregation", "Merging",
               "Time Series", "Pivot Tables", "String Methods", "Apply/Map", "IO"],
    "NumPy": ["Arrays", "Operations", "Indexing", "Broadcasting", "Linear Algebra",
              "Random", "Reshaping", "Stacking", "Universal Functions"],
    "Polars": ["DataFrames", "Expressions", "Lazy Frames", "GroupBy", "Joins", "IO"],
    "SciPy": ["Statistics", "Optimization", "Interpolation", "Signal Processing", "Linear Algebra"],
    # ━━ VISUALIZATION ━━
    "Matplotlib": ["Line Plots", "Bar Charts", "Scatter Plots", "Subplots", "Styling",
                   "Annotations", "Histograms", "Heatmaps", "3D Plots"],
    "Seaborn": ["Distribution Plots", "Categorical Plots", "Regression Plots",
                "Heatmaps", "Pair Plots", "Styling"],
    "Plotly": ["Line Charts", "Bar Charts", "Scatter Plots", "Dashboards",
               "Maps", "3D Plots", "Animations"],
    # ━━ MACHINE LEARNING ━━
    "Scikit-learn": ["Preprocessing", "Classification", "Regression", "Clustering",
                     "Model Evaluation", "Pipelines", "Feature Selection", "Cross Validation"],
    "PyTorch": ["Tensors", "Autograd", "Neural Networks", "Training Loops",
                "Datasets", "Transforms", "CNNs", "RNNs", "Transfer Learning"],
    "XGBoost": ["DMatrix", "Training", "Parameters", "Feature Importance",
                "Cross Validation", "Early Stopping"],
    "MLflow": ["Tracking", "Projects", "Models", "Registry", "Deployment"],
    "ML Deployment": ["Model Serialization", "API Serving", "Batch Inference",
                      "Monitoring", "A/B Testing"],
    # ━━ FILE FORMATS & EXCEL ━━
    "openpyxl": ["Reading", "Writing", "Formatting", "Charts", "Formulas", "Sheets",
                 "Styles", "Conditional Formatting", "Data Validation", "Macros"],
    "CSV": ["Reading", "Writing", "DictReader", "DictWriter", "Dialects", "Large Files"],
    "JSON": ["Loads", "Dumps", "File IO", "Custom Encoders", "Nested Data", "Streaming"],
    # ━━ WEB & HTTP ━━
    "Requests": ["GET", "POST", "Headers", "Authentication", "Sessions", "Error Handling"],
    "HTTP": ["Methods", "Headers", "Status Codes", "CORS", "TLS", "Cookies", "WebSockets"],
    # ━━ WEB SCRAPING ━━
    "BeautifulSoup": ["Parsing HTML", "Find Elements", "CSS Selectors", "Navigation",
                      "Text Extraction", "Attributes"],
    "Selenium": ["WebDriver", "Locators", "Waits", "Actions", "Forms", "Screenshots"],
    # ━━ CLI & AUTOMATION ━━
    "Click": ["Commands", "Arguments", "Options", "Groups", "Prompts", "Output"],
    "Typer": ["Commands", "Arguments", "Options", "Callbacks", "Testing"],
    # ━━ TESTING & QUALITY ━━
    "Pytest": ["Test Functions", "Fixtures", "Parametrize", "Mocking", "Markers",
               "Conftest", "Coverage", "Plugins"],
    "Pydantic": ["Models", "Validation", "Serialization", "Settings", "Custom Types", "Nested Models"],
    # ━━ ASYNC ━━
    "asyncio": ["Coroutines", "Tasks", "Event Loop", "Gather", "Queues",
                "Locks", "Timeouts", "Streams"],
    # ━━ DEVOPS & INFRASTRUCTURE ━━
    "Git": ["Commits", "Branches", "Merging", "Rebasing", "Stashing",
            "Workflows", "Hooks", "Cherry-pick"],
    "Docker": ["Images", "Containers", "Volumes", "Networks", "Compose",
               "Multi-stage Builds", "Registry", "Debugging"],
    "Linux CLI": ["Navigation", "Permissions", "Pipes", "Processes", "Cron",
                  "SSH", "Shell Scripting", "Package Management"],
    "AWS": ["EC2", "S3", "Lambda", "RDS", "IAM", "API Gateway", "SQS", "CloudWatch"],
    "CI/CD": ["GitHub Actions", "Pipelines", "Testing", "Deployment", "Environments"],
    # ━━ ARCHITECTURE & CONCEPTS ━━
    "Authentication": ["JWT", "OAuth2", "Sessions", "RBAC", "API Keys", "MFA"],
    "System Design": ["Load Balancing", "Caching", "Queues", "Microservices",
                      "Monoliths", "Scaling", "Database Sharding"],
    # ━━ NLP & TEXT ━━
    "spaCy": ["Tokenization", "NER", "POS Tagging", "Dependency Parsing",
              "Pipelines", "Custom Components"],
    "Regex": ["Patterns", "Match", "Search", "Findall", "Sub", "Groups", "Lookahead"],
    # ━━ IMAGE & MEDIA ━━
    "Pillow": ["Open", "Resize", "Crop", "Filters", "Draw", "Text", "Formats"],
    "OpenCV": ["Image IO", "Color Spaces", "Thresholding", "Contours",
               "Transformations", "Video", "Face Detection"],
    # ━━ UI ━━
    "Streamlit": ["Layout", "Widgets", "State Management", "Charts", "Data Display"],
    # ━━ SYSTEMS LANGUAGES ━━
    "C#": ["Variables", "Types", "Classes", "Interfaces", "Inheritance", "Properties",
           "Methods", "Collections", "LINQ", "Async/Await", "Exception Handling",
           "Delegates", "Events", "Generics", "Nullable Types", "Pattern Matching"],
    "Rust": ["Ownership", "Borrowing", "Structs", "Enums", "Pattern Matching",
             "Traits", "Lifetimes", "Error Handling", "Iterators", "Concurrency"],
    "Go": ["Variables", "Functions", "Structs", "Interfaces", "Goroutines",
           "Channels", "Error Handling", "Packages", "Slices", "Maps"],
}
