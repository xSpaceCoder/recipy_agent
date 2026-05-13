from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_supabase
from app.auth import get_current_user

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


class Ingredient(BaseModel):
    name: str
    quantity: str = ""
    unit: str = ""


class RecipeCreate(BaseModel):
    title: str
    description: str | None = None
    ingredients: list[Ingredient] = []
    instructions: list[str] = []
    servings: int | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    bake_time_minutes: int | None = None
    tags: list[str] = []
    category: str | None = None
    season: list[str] = ["all"]
    rating: int | None = None
    visibility: str = "public"
    source_type: str = "manual"


def _strip_private_fields(recipe: dict, user_id: str) -> dict:
    if recipe.get("user_id") != user_id:
        recipe.pop("rating", None)
    return recipe


@router.get("/")
async def list_recipes(category: str | None = None, search: str | None = None, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    query = sb.table("recipes").select("*").or_(
        f"user_id.eq.{user['id']},visibility.eq.public"
    ).order("created_at", desc=True)

    if category:
        query = query.eq("category", category)

    if search:
        query = query.text_search("fts", search, options={"type": "websearch"})

    result = query.execute()
    return [_strip_private_fields(r, user["id"]) for r in result.data]


@router.get("/{recipe_id}")
async def get_recipe(recipe_id: str, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = sb.table("recipes").select("*").eq("id", recipe_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Recipe not found")
    recipe = result.data[0]
    if recipe["user_id"] != user["id"] and recipe.get("visibility") != "public":
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _strip_private_fields(recipe, user["id"])


@router.post("/", status_code=201)
async def create_recipe(recipe: RecipeCreate, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    data = recipe.model_dump()
    data["ingredients"] = [ing.model_dump() for ing in recipe.ingredients]
    data["user_id"] = user["id"]
    result = sb.table("recipes").insert(data).execute()
    return result.data[0]


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: str, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = sb.table("recipes").select("user_id").eq("id", recipe_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if result.data[0]["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own recipes")
    sb.table("recipes").delete().eq("id", recipe_id).execute()
