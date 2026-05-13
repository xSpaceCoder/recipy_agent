import { useState } from 'react'
import { AuthProvider, useAuth } from './lib/useAuth'
import LoginPage from './components/LoginPage'
import RecipeForm from './components/RecipeForm'
import RecipeIngest from './components/RecipeIngest'
import RecipeList from './components/RecipeList'

function AppContent() {
  const { user, loading, signOut } = useAuth()
  const [view, setView] = useState('list')
  const [refreshKey, setRefreshKey] = useState(0)
  const [editingRecipe, setEditingRecipe] = useState(null)

  if (loading) return <div className="status">Loading...</div>
  if (!user) return <LoginPage />

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
          <button className="sign-out-btn" onClick={signOut}>
            Sign Out
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

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
