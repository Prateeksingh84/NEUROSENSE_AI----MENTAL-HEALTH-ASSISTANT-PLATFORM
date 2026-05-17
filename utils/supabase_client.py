import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    ""
).strip()

if not SUPABASE_URL:
    raise ValueError(
        "SUPABASE_URL missing in .env"
    )

if not SUPABASE_ANON_KEY:
    raise ValueError(
        "SUPABASE_ANON_KEY missing in .env"
    )

if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError(
        "SUPABASE_SERVICE_ROLE_KEY missing in .env"
    )

# ============================================================================
# PUBLIC CLIENT
# ============================================================================

supabase_public: Client = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
)

# ============================================================================
# SERVICE ROLE CLIENT
# ============================================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)