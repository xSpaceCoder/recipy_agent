import { useState } from 'react'
import RecipeForm from './components/RecipeForm'
import RecipeIngest from './components/RecipeIngest'
import RecipeList from './components/RecipeList'

function App() {
  const [view, setView] = useState('list')
  const [refreshKey, setRefreshKey] = useState(0)

  const handleRecipeSaved = () => {
    setRefreshKey(k => k + 1)
    setView('list')
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Recipe Agent</h1>
        <nav>
          <button
            className={view === 'list' ? 'active' : ''}
            onClick={() => setView('list')}
          >
            Recipes
          </button>
          <button
            className={view === 'import' ? 'active' : ''}
            onClick={() => setView('import')}
          >
            Import
          </button>
          <button
            className={view === 'add' ? 'active' : ''}
            onClick={() => setView('add')}
          >
            + Manual
          </button>
        </nav>
      </header>
      <main>
        {view === 'list' && <RecipeList key={refreshKey} />}
        {view === 'import' && <RecipeIngest onSaved={handleRecipeSaved} />}
        {view === 'add' && <RecipeForm onSaved={handleRecipeSaved} />}
      </main>
    </div>
  )
}

export default App
