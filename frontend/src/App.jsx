import { useState, useRef, useEffect } from 'react'
import { AuthProvider, useAuth } from './lib/useAuth'
import LoginPage from './components/LoginPage'
import RecipeForm from './components/RecipeForm'
import RecipeIngest from './components/RecipeIngest'
import RecipeList from './components/RecipeList'

function ProfileMenu() {
  const { user, signOut } = useAuth()
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const avatarUrl = user?.user_metadata?.avatar_url
  const displayName = user?.user_metadata?.full_name || user?.email || 'User'

  return (
    <div className="profile-menu" ref={menuRef}>
      <button className="profile-btn" onClick={() => setOpen(!open)}>
        {avatarUrl ? (
          <img src={avatarUrl} alt="" className="profile-avatar" />
        ) : (
          <svg className="profile-avatar-placeholder" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
          </svg>
        )}
      </button>
      {open && (
        <div className="profile-dropdown">
          <div className="profile-name">{displayName}</div>
          <button className="profile-signout" onClick={signOut}>Sign Out</button>
        </div>
      )}
    </div>
  )
}

function AppContent() {
  const { user, loading } = useAuth()
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
        <div className="header-brand" onClick={() => { setEditingRecipe(null); setView('list') }}>
          <img src="/icon/favicon.png" alt="" className="header-logo" />
          <h1>Nexxt Bite</h1>
        </div>
        <nav>
          <button
            className={view === 'import' ? 'active' : ''}
            onClick={() => { setEditingRecipe(null); setView('import') }}
          >
            +
          </button>
          <ProfileMenu />
        </nav>
      </header>
      <main>
        {view === 'list' && <RecipeList key={refreshKey} onEdit={handleEdit} />}
        {view === 'import' && <RecipeIngest onSaved={handleRecipeSaved} />}
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
