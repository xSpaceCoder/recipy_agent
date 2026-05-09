from supabase import create_client
from app.config import get_settings


def get_supabase():
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
