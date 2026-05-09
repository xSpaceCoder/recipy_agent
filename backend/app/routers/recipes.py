from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_supabase

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
    source_type: str = "manual"


@router.get("/")
async def list_recipes(category: str | None = None, search: str | None = None):
    sb = get_supabase()
    query = sb.table("recipes").select("*").order("created_at", desc=True)

    if category:
        query = query.eq("category", category)

    if search:
        query = query.text_search("fts", search, options={"type": "websearch"})

    result = query.execute()
    return result.data


@router.get("/{recipe_id}")
async def get_recipe(recipe_id: str):
    sb = get_supabase()
    result = sb.table("recipes").select("*").eq("id", recipe_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return result.data[0]


@router.post("/", status_code=201)
async def create_recipe(recipe: RecipeCreate):
    sb = get_supabase()
    data = recipe.model_dump()
    data["ingredients"] = [ing.model_dump() for ing in recipe.ingredients]
    result = sb.table("recipes").insert(data).execute()
    return result.data[0]


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: str):
    sb = get_supabase()
    sb.table("recipes").delete().eq("id", recipe_id).execute()
