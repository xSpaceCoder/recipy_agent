# Implementation Guide: Recipe Consultation (Natural Language Search)

## Goal
Enhance the existing search bar to understand natural language queries in both German and English. When a query looks like a sentence (auto-detected), route it through the backend where Gemini translates and expands the query, then return the full recipe list reordered by relevance with 1-sentence explanations for top matches. If results are poor, show a conversational fallback prompt.

## Design Decisions (Already Agreed)

| Aspect | Decision |
|--------|----------|
| Entry point | Existing search bar in RecipeList component |
| Detection | Auto-detect: if query is >3 words or contains verbs/natural phrasing, route to AI backend; otherwise use existing Supabase full-text search |
| Bilingual | Query-time: Gemini translates query into both DE + EN search terms |
| Context | Current season + German produce seasonality included in prompt |
| Results | Full recipe list reordered, best matches on top |
| Response | 1-sentence explanation per top match (why it fits) |
| Language | Agent responds in the language of the user's query |
| Fallback | If <2 matches, show: "No great matches — want me to help you find something?" |
| Cook history | Deferred to later (cook_log table) |

## Architecture

```
User types query in search bar
        │
        ▼
Frontend auto-detects: NL query or keyword?
        │
   ┌────┴────┐
   │         │
Keyword    NL Query
   │         │
   ▼         ▼
Supabase   POST /api/recipes/consult
textSearch    │
(existing)    ▼
           Gemini expands query:
           - Translate to DE + EN keywords
           - Extract: tags, category, season, time constraints
           - Consider current season + German produce seasonality
              │
              ▼
           Backend queries Supabase with expanded filters
              │
              ▼
           Gemini ranks results + generates 1-sentence explanations
              │
              ▼
           Return: ordered recipe list + explanations + fallback flag
```

## Implementation Steps

### Step 1: Backend — Consultation Endpoint

**File to create**: `backend/app/routers/consultation.py`

```python
# New router: POST /api/recipes/consult
# Input: { "query": "something quick with rice", "recipe_ids": [...] }
# - query: the user's natural language input
# - recipe_ids: optional, all recipe IDs the user currently has access to
#   (or fetch server-side using user's JWT)
#
# Flow:
# 1. Fetch all user-accessible recipes from Supabase (own + public)
# 2. Send to Gemini with the consultation prompt
# 3. Return ranked recipe IDs + explanations
```

**Endpoint signature**:
```python
@router.post("/api/recipes/consult")
async def consult_recipes(
    request: ConsultRequest,
    user: dict = Depends(get_current_user)
) -> ConsultResponse
```

**Pydantic models**:
```python
class ConsultRequest(BaseModel):
    query: str  # natural language query

class RecipeMatch(BaseModel):
    recipe_id: str
    explanation: str  # 1-sentence reason in user's language

class ConsultResponse(BaseModel):
    matches: list[RecipeMatch]  # ordered by relevance, ALL recipes
    fallback: bool  # true if <2 good matches
```

### Step 2: Backend — Consultation AI Service

**File to create**: `backend/app/services/consultation.py`

This service builds the Gemini prompt and parses the response.

**Prompt strategy** (two-step):

1. **Step 1 — Query Understanding** (could be combined into one call):
   Send Gemini the user's query + current date + season info. Ask it to output:
   - Detected language (de/en)
   - Search keywords in BOTH DE and EN
   - Relevant filters: tags, category, season, max_time
   - Intent: what the user is really looking for

2. **Step 2 — Recipe Ranking**:
   Send Gemini:
   - The parsed intent from step 1
   - A condensed list of all user-accessible recipes (id, title, tags, category, season, prep_time, ingredients summary)
   - Current date + season context (including German produce seasonality)
   - Ask it to rank ALL recipes by relevance and provide 1-sentence explanation for the top 5

**Optimization**: Combine into a single Gemini call to save latency. Send the query + recipe summaries together. Gemini returns ranked IDs + explanations.

**Season context to include in prompt**:
```
Current date: {date}
Season: {spring/summer/autumn/winter}
German seasonal produce right now: {list based on month}
```

**German seasonal produce reference** (embed in prompt by month):
- Jan-Feb: root vegetables, cabbage, leeks, stored apples
- Mar-Apr: rhubarb, asparagus, spinach, wild garlic
- May-Jun: strawberries, asparagus, peas, radishes, herbs
- Jul-Aug: berries, tomatoes, zucchini, peppers, stone fruit
- Sep-Oct: pumpkin, mushrooms, apples, pears, plums, grapes
- Nov-Dec: cabbage, root vegetables, nuts, citrus (imported)

### Step 3: Backend — Register the Router

**File to modify**: `backend/app/main.py`

```python
from app.routers import recipes, ingestion, consultation

app.include_router(consultation.router)
```

### Step 4: Frontend — Auto-Detection Logic

**File to modify**: `frontend/src/components/RecipeList.jsx`

Add a helper function to detect NL queries:

```javascript
function isNaturalLanguageQuery(query) {
  const trimmed = query.trim()
  const words = trimmed.split(/\s+/)
  
  // Heuristic: 4+ words likely means a sentence/phrase
  if (words.length >= 4) return true
  
  // Common NL indicators in German and English
  const nlIndicators = [
    // German
    /^(ich |was |etwas |etwas |etwas |mir |heute |schnell |gibt es)/i,
    /( mit | ohne | für | aus | und | oder | nicht | kein)/i,
    // English  
    /^(i |what |something |give me|tonight|quick|show me)/i,
    /( with | without | for | and | or | not | no )/i,
    // Question words
    /^(was|what|welche|which|wie|how)\b/i,
  ]
  
  return nlIndicators.some(pattern => pattern.test(trimmed))
}
```

### Step 5: Frontend — Call Consultation Endpoint

**File to modify**: `frontend/src/components/RecipeList.jsx`

Modify `handleSearch()`:

```javascript
async function handleSearch() {
  const query = search.trim()
  if (!query) { fetchRecipes(); return }
  
  if (isNaturalLanguageQuery(query)) {
    // Route to AI consultation
    setLoading(true)
    try {
      const { data: { session } } = await supabase.auth.getSession()
      const response = await fetch(`${BACKEND_URL}/api/recipes/consult`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ query })
      })
      const result = await response.json()
      
      // Reorder recipes by AI ranking
      const orderedRecipes = result.matches.map(match => ({
        ...recipes.find(r => r.id === match.recipe_id),
        ai_explanation: match.explanation
      })).filter(Boolean)
      
      // Append unmatched recipes at the bottom
      const matchedIds = new Set(result.matches.map(m => m.recipe_id))
      const unmatched = recipes.filter(r => !matchedIds.has(r.id))
      
      setRecipes([...orderedRecipes, ...unmatched])
      setShowFallback(result.fallback)
    } catch (err) {
      console.error('Consultation failed:', err)
      // Fall back to regular text search
      handleTextSearch(query)
    } finally {
      setLoading(false)
    }
  } else {
    // Existing Supabase full-text search
    handleTextSearch(query)
  }
}
```

### Step 6: Frontend — Display AI Explanations

Show the 1-sentence explanation on recipe cards when present:

```jsx
{recipe.ai_explanation && (
  <p className="ai-explanation">{recipe.ai_explanation}</p>
)}
```

Style it as a subtle italic line below the recipe title in the card.

### Step 7: Frontend — Conversational Fallback

When `showFallback` is true and results are sparse:

```jsx
{showFallback && (
  <div className="consultation-fallback">
    <p>No great matches — want me to help you find something?</p>
    <button onClick={() => setShowChat(true)}>Yes, help me</button>
  </div>
)}
```

The conversational mode can be a simple 1-2 message exchange (not a full chat UI). Defer complex chat to a later iteration.

### Step 8: Frontend — Environment Variable

Ensure `BACKEND_URL` is available in the frontend (likely already configured for ingestion calls). Check how existing ingestion components call the backend and follow the same pattern.

## File Summary

| Action | File |
|--------|------|
| Create | `backend/app/routers/consultation.py` |
| Create | `backend/app/services/consultation.py` |
| Modify | `backend/app/main.py` (register router) |
| Modify | `frontend/src/components/RecipeList.jsx` (auto-detect + AI search + fallback UI) |
| Modify | `frontend/src/components/RecipeCard.jsx` (show AI explanation) |

## Important Notes

- **No new packages needed** — uses existing `google-generativeai` SDK and `supabase` client
- **Backend fetches all recipes server-side** — don't send recipe data from frontend (security + simplicity)
- **Condensed recipe summaries for Gemini** — don't send full instructions, just title + tags + category + season + prep_time + ingredient names. This keeps the prompt small and fast.
- **Error fallback** — if AI consultation fails, silently fall back to existing text search
- **CORS** — the `/api/recipes/consult` endpoint is on the same backend as ingestion, so CORS is already configured
- **Rate limiting consideration** — each NL search = 1 Gemini API call. This is fine for personal use with friends/family.

## Testing Checklist

- [ ] German query ("etwas schnelles mit Reis") returns German + English rice recipes
- [ ] English query ("something quick with lentils") returns recipes with "Linsen" too
- [ ] Season-aware: summer query prefers light/seasonal recipes
- [ ] Fallback appears when no good matches exist
- [ ] Regular keyword search still works (1-2 word queries bypass AI)
- [ ] Auth token is passed correctly to consultation endpoint
- [ ] Graceful degradation: if backend is down, text search still works
