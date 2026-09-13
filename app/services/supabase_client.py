from functools import lru_cache

from app.core.config import (
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
    supabase_configured,
)


class SupabaseNotConfiguredError(Exception):
    pass


@lru_cache(maxsize=1)
def get_supabase():
    if not supabase_configured():
        raise SupabaseNotConfiguredError(
            "Supabase no está configurado. Revisa SUPABASE_URL y "
            "SUPABASE_SERVICE_ROLE_KEY."
        )
    from supabase import create_client

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
