import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../lib/useAuth'
import RecipeCard from './RecipeCard'

function RecipeList({ onEdit }) {
  const { user } = useAuth()
  const [recipes, setRecipes] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')

  useEffect(() => {
    fetchRecipes()
  }, [categoryFilter])

  const fetchRecipes = async () => {
    setLoading(true)
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
    }
    setLoading(false)
  }

  const handleSearch = async () => {
    if (!search.trim()) {
      fetchRecipes()
      return
    }
    setLoading(true)
    const { data, error } = await supabase
      .from('recipes')
      .select('*')
      .textSearch('fts', search.trim(), { type: 'websearch' })
      .order('created_at', { ascending: false })

    if (!error) {
      setRecipes(data || [])
    }
    setLoading(false)
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

      {loading ? (
        <p className="status">Loading...</p>
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
