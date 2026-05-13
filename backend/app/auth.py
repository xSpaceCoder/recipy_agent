from fastapi import Depends, HTTPException, Request
from supabase import create_client
from app.config import get_settings


def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.split(" ", 1)[1]
    settings = get_settings()
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)

    try:
        response = sb.auth.get_user(token)
        return {"id": response.user.id, "email": response.user.email}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
