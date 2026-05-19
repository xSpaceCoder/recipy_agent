import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_supabase
from app.services.consultation import consult_recipes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recipes", tags=["consultation"])


class ConsultRequest(BaseModel):
    query: str


class RecipeMatch(BaseModel):
    recipe_id: str
    explanation: str


class ConsultResponse(BaseModel):
    matches: list[RecipeMatch]
    fallback: bool


@router.post("/consult", response_model=ConsultResponse)
async def consult(request: ConsultRequest, user: dict = Depends(get_current_user)):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    sb = get_supabase()
    response = sb.table("recipes").select("*").or_(
        f"user_id.eq.{user['id']},visibility.eq.public"
    ).execute()

    recipes = response.data or []
    logger.info(f"Consulting {len(recipes)} recipes for user {user['id']}")

    try:
        result = consult_recipes(request.query, recipes)
    except Exception as e:
        logger.error(f"Consultation AI failed: {e}")
        raise HTTPException(status_code=502, detail="AI consultation temporarily unavailable")

    matches = [
        RecipeMatch(recipe_id=m["recipe_id"], explanation=m.get("explanation", ""))
        for m in result.get("matches", [])
    ]

    return ConsultResponse(matches=matches, fallback=result.get("fallback", False))
