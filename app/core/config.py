import os

from dotenv import load_dotenv


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_ANON_KEY = (os.getenv("SUPABASE_ANON_KEY") or "").strip()
SUPABASE_SERVICE_ROLE_KEY = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
AGENT_USER_ID = (os.getenv("AGENT_USER_ID") or "").strip() or None
AGENT_BOOTSTRAP_EMAIL = (os.getenv("AGENT_BOOTSTRAP_EMAIL") or "").strip() or None
AGENT_BOOTSTRAP_PASSWORD = (os.getenv("AGENT_BOOTSTRAP_PASSWORD") or "").strip() or None
SUPABASE_CV_BUCKET = (os.getenv("SUPABASE_CV_BUCKET") or "cv-files").strip()


def supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)
