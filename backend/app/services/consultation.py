import json
import logging
from datetime import date

import google.generativeai as genai
from app.config import get_settings

logger = logging.getLogger(__name__)

SEASONAL_PRODUCE = {
    1: "root vegetables, cabbage, leeks, stored apples",
    2: "root vegetables, cabbage, leeks, stored apples",
    3: "rhubarb, asparagus, spinach, wild garlic",
    4: "rhubarb, asparagus, spinach, wild garlic",
    5: "strawberries, asparagus, peas, radishes, herbs",
    6: "strawberries, asparagus, peas, radishes, herbs",
    7: "berries, tomatoes, zucchini, peppers, stone fruit",
    8: "berries, tomatoes, zucchini, peppers, stone fruit",
    9: "pumpkin, mushrooms, apples, pears, plums, grapes",
    10: "pumpkin, mushrooms, apples, pears, plums, grapes",
    11: "cabbage, root vegetables, nuts, citrus (imported)",
    12: "cabbage, root vegetables, nuts, citrus (imported)",
}

SEASONS_BY_MONTH = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
}


def _get_model():
    settings = get_settings()
    genai.configure(api_key=settings.google_ai_api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


def _build_consultation_prompt(query: str, recipes_summary: list[dict]) -> str:
    today = date.today()
    month = today.month
    season = SEASONS_BY_MONTH[month]
    produce = SEASONAL_PRODUCE[month]

    recipes_text = "\n".join(
        f"- ID: {r['id']} | Title: {r['title']} | Tags: {', '.join(r.get('tags') or [])} | "
        f"Category: {r.get('category', '')} | Season: {', '.join(r.get('season') or [])} | "
        f"Prep: {r.get('prep_time_minutes', '?')} min | "
        f"Ingredients: {', '.join(ing['name'] for ing in (r.get('ingredients') or []))}"
        for r in recipes_summary
    )

    return f"""You are a recipe consultation assistant. The user is searching their personal recipe collection using natural language.

Context:
- Today's date: {today.isoformat()}
- Current season: {season}
- German seasonal produce available now: {produce}
- The user is vegetarian (no meat, no fish)

User's query: "{query}"

Available recipes:
{recipes_text}

Your task:
1. Understand what the user is looking for (ingredients, mood, time constraints, occasion, season preferences)
2. Rank ALL recipes by relevance to the query. Put the best matches first.
3. For the top 5 matches, provide a short 1-sentence explanation of why it fits.
4. If fewer than 2 recipes are a good match, set "fallback" to true.
5. Respond in the SAME LANGUAGE as the user's query (German query → German explanations, English query → English explanations).

Return ONLY valid JSON with this structure (no markdown, no code fences):
{{
  "matches": [
    {{"recipe_id": "uuid-here", "explanation": "Short reason why this fits (only for top 5, empty string for others)"}},
    ...
  ],
  "fallback": false
}}

Include ALL recipes in the matches array, ordered by relevance. Only the top 5 need explanations."""


def consult_recipes(query: str, recipes: list[dict]) -> dict:
    if not recipes:
        return {"matches": [], "fallback": True}

    recipes_summary = [
        {
            "id": r["id"],
            "title": r["title"],
            "tags": r.get("tags"),
            "category": r.get("category"),
            "season": r.get("season"),
            "prep_time_minutes": r.get("prep_time_minutes"),
            "ingredients": r.get("ingredients"),
        }
        for r in recipes
    ]

    prompt = _build_consultation_prompt(query, recipes_summary)
    model = _get_model()

    logger.info(f"Consulting recipes for query: {query}")
    response = model.generate_content(prompt)
    logger.debug(f"Consultation response: {response.text[:500]}")

    return _parse_response(response.text)


def _parse_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned)
