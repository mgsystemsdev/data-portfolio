import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"
DB_PATH = os.path.join(os.path.dirname(__file__), "apprentice.db")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
