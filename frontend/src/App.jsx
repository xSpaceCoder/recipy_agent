import { useState } from 'react'
import RecipeForm from './components/RecipeForm'
import RecipeIngest from './components/RecipeIngest'
import RecipeList from './components/RecipeList'

function App() {
  const [view, setView] = useState('list')
  const [refreshKey, setRefreshKey] = useState(0)
  const [editingRecipe, setEditingRecipe] = useState(null)

  const handleRecipeSaved = () => {
    setRefreshKey(k => k + 1)
    setEditingRecipe(null)
    setView('list')
  }

  const handleEdit = (recipe) => {
    setEditingRecipe(recipe)
    setView('edit')
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Recipe Agent</h1>
        <nav>
          <button
            className={view === 'list' ? 'active' : ''}
            onClick={() => { setEditingRecipe(null); setView('list') }}
          >
            Recipes
          </button>
          <button
            className={view === 'import' ? 'active' : ''}
            onClick={() => { setEditingRecipe(null); setView('import') }}
          >
            Import
          </button>
          <button
            className={view === 'add' ? 'active' : ''}
            onClick={() => { setEditingRecipe(null); setView('add') }}
          >
            + Manual
          </button>
        </nav>
      </header>
      <main>
        {view === 'list' && <RecipeList key={refreshKey} onEdit={handleEdit} />}
        {view === 'import' && <RecipeIngest onSaved={handleRecipeSaved} />}
        {view === 'add' && <RecipeForm onSaved={handleRecipeSaved} />}
        {view === 'edit' && editingRecipe && (
          <RecipeForm key={editingRecipe.id} recipe={editingRecipe} onSaved={handleRecipeSaved} />
        )}
      </main>
    </div>
  )
}

export default App
