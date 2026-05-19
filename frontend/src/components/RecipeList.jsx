import { useState, useEffect, useRef } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../lib/useAuth'
import RecipeCard from './RecipeCard'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function isNaturalLanguageQuery(query) {
  const trimmed = query.trim()
  const words = trimmed.split(/\s+/)

  if (words.length >= 4) return true

  const nlIndicators = [
    /^(ich |was |etwas |mir |heute |schnell |gibt es)/i,
    /( mit | ohne | für | aus | und | oder | nicht | kein)/i,
    /^(i |what |something |give me|tonight|quick|show me)/i,
    /( with | without | for | and | or | not | no )/i,
    /^(was|what|welche|which|wie|how)\b/i,
  ]

  return nlIndicators.some(pattern => pattern.test(trimmed))
}

function RecipeList({ onEdit }) {
  const { user } = useAuth()
  const [recipes, setRecipes] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [showFallback, setShowFallback] = useState(false)
  const [isAiSearch, setIsAiSearch] = useState(false)
  const allRecipesRef = useRef([])

  useEffect(() => {
    fetchRecipes()
  }, [categoryFilter])

  const fetchRecipes = async () => {
    setLoading(true)
    setShowFallback(false)
    setIsAiSearch(false)
    let query = supabase
      .from('recipes')
      .select('*')
      .order('created_at', { ascending: false })

    if (categoryFilter) {
      query = query.eq('category', categoryFilter)
    }

    const { data, error } = await query

    if (!error) {
      setRecipes(data || [])
      allRecipesRef.current = data || []
    }
    setLoading(false)
  }

  const handleTextSearch = async (term) => {
    setLoading(true)
    const { data, error } = await supabase
      .from('recipes')
      .select('*')
      .textSearch('fts', term, { type: 'websearch' })
      .order('created_at', { ascending: false })

    if (!error) {
      setRecipes(data || [])
    }
    setLoading(false)
  }

  const handleSearch = async () => {
    const query = search.trim()
    if (!query) {
      fetchRecipes()
      return
    }

    if (isNaturalLanguageQuery(query)) {
      setLoading(true)
      setIsAiSearch(true)
      setShowFallback(false)
      try {
        const { data: { session } } = await supabase.auth.getSession()
        const response = await fetch(`${API_URL}/api/recipes/consult`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`
          },
          body: JSON.stringify({ query })
        })

        if (!response.ok) throw new Error(`Status ${response.status}`)

        const result = await response.json()

        const orderedRecipes = result.matches.map(match => ({
          ...allRecipesRef.current.find(r => r.id === match.recipe_id),
          ai_explanation: match.explanation || undefined
        })).filter(r => r && r.id)

        const matchedIds = new Set(result.matches.map(m => m.recipe_id))
        const unmatched = allRecipesRef.current.filter(r => !matchedIds.has(r.id))

        setRecipes([...orderedRecipes, ...unmatched])
        setShowFallback(result.fallback)
      } catch (err) {
        console.error('Consultation failed, falling back to text search:', err)
        setIsAiSearch(false)
        await handleTextSearch(query)
      } finally {
        setLoading(false)
      }
    } else {
      setIsAiSearch(false)
      setShowFallback(false)
      await handleTextSearch(query)
    }
  }

  const handleDelete = async (id) => {
    const { error } = await supabase.from('recipes').delete().eq('id', id)
    if (!error) {
      setRecipes(r => r.filter(recipe => recipe.id !== id))
    }
  }

  return (
    <div className="recipe-list">
      <div className="search-bar">
        <input
          type="search"
          placeholder="Search recipes..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
        />
        <button onClick={handleSearch}>Search</button>
      </div>

      <div className="filters">
        <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
          <option value="">All categories</option>
          <option value="dinner">Dinner</option>
          <option value="cake">Cake</option>
          <option value="dessert">Dessert</option>
          <option value="soup/stew">Soup/Stew</option>
          <option value="breakfast">Breakfast</option>
          <option value="snack">Snack</option>
        </select>
      </div>

      {showFallback && (
        <div className="consultation-fallback">
          <p>No great matches found. Try rephrasing your query or browse all recipes.</p>
        </div>
      )}

      {loading ? (
        <p className="status">{isAiSearch ? 'Thinking...' : 'Loading...'}</p>
      ) : recipes.length === 0 ? (
        <p className="status">No recipes yet. Add your first one!</p>
      ) : (
        <div className="recipe-grid">
          {recipes.map(recipe => (
            <RecipeCard key={recipe.id} recipe={recipe} onDelete={handleDelete} onEdit={onEdit} isOwner={recipe.user_id === user?.id} />
          ))}
        </div>
      )}
    </div>
  )
}

export default RecipeList
