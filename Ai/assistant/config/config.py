"""Minimal config: env vars and defaults."""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "assistant.db"))
