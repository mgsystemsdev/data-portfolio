import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"
DB_PATH = os.path.join(os.path.dirname(__file__), "apprentice.db")

# DOCS_DIR should point to the folder containing:
#   prompt_pract_v1.md
#   knowledge_file_v7.md
DOCS_DIR = os.path.dirname(__file__)
