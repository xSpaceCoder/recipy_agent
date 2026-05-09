import json
import logging
import google.generativeai as genai
from app.config import get_settings

logger = logging.getLogger(__name__)

RECIPE_PARSE_PROMPT = """You are a recipe extraction assistant. Extract the recipe from the provided content and return it as a JSON object.

IMPORTANT: The user is vegetarian (no meat, no fish). If the recipe contains meat or fish, set "is_vegetarian": false in the response. Otherwise set "is_vegetarian": true.

Return ONLY valid JSON with this exact structure (no markdown, no code fences):
{
  "title": "Recipe title",
  "description": "Brief 1-2 sentence description",
  "ingredients": [
    {"name": "ingredient name", "quantity": "amount", "unit": "unit of measurement"}
  ],
  "instructions": ["Step 1 text", "Step 2 text"],
  "servings": number,
  "prep_time_minutes": number or null,
  "cook_time_minutes": number or null,
  "bake_time_minutes": number or null,
  "tags": ["vegetarian", "other relevant tags like: vegan, gluten-free, light, cozy, fiber-rich, quick, meal-prep"],
  "category": "one of: dinner, cake, dessert, soup/stew, breakfast, snack",
  "season": ["relevant seasons: spring, summer, autumn, winter, or all"],
  "is_vegetarian": true/false
}

If information is missing, estimate reasonable values. For tags, always include dietary tags that apply, use englsih only tags.
Use either german or english as your output language. Calculate all american quantities and units into the metric system. You may still use table spoon, tee spoon and other common german/european measurements. 
If you cannot extract a recipe from the content, return: {"error": "Could not extract recipe from the provided content"}
"""


def get_model():
    settings = get_settings()
    genai.configure(api_key=settings.google_ai_api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


def parse_recipe_from_text(content: str) -> dict:
    model = get_model()
    response = model.generate_content([
        RECIPE_PARSE_PROMPT,
        f"Here is the content to extract a recipe from:\n\n{content}"
    ])
    return _parse_response(response.text)


def parse_recipe_from_video(url: str) -> dict:
    logger.info(f"Sending video URL to Gemini for analysis: {url}")
    model = get_model()
    response = model.generate_content([
        RECIPE_PARSE_PROMPT,
        "Watch this video and extract the recipe from it. Analyze the visual content, "
        "any voice-over/narration, and on-screen text to identify ingredients and steps.",
        {"file_data": {"file_uri": url, "mime_type": "video/*"}}
    ])
    logger.debug(f"Gemini video response: {response.text[:300]}")
    return _parse_response(response.text)


def parse_recipe_from_image(image_bytes: bytes, mime_type: str) -> dict:
    model = get_model()
    response = model.generate_content([
        RECIPE_PARSE_PROMPT,
        {"mime_type": mime_type, "data": image_bytes}
    ])
    return _parse_response(response.text)


def parse_recipe_from_images(images: list[dict]) -> dict:
    model = get_model()
    parts = [RECIPE_PARSE_PROMPT]
    for img in images:
        parts.append({"mime_type": img["mime_type"], "data": img["data"]})
    parts.append("Extract the recipe from these image(s).")
    response = model.generate_content(parts)
    return _parse_response(response.text)


def _parse_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned)
