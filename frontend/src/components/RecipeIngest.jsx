import { useState } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../lib/useAuth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function RecipeIngest({ onSaved }) {
  const { user } = useAuth()
  const [mode, setMode] = useState('url')
  const [url, setUrl] = useState('')
  const [files, setFiles] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [preview, setPreview] = useState(null)

  const getAuthHeaders = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token
      ? { Authorization: `Bearer ${session.access_token}` }
      : {}
  }

  const handleIngestUrl = async () => {
    setLoading(true)
    setError(null)
    try {
      const endpoint = mode === 'youtube' ? '/api/ingest/youtube' : '/api/ingest/url'
      const authHeaders = await getAuthHeaders()
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        body: JSON.stringify({ url }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Ingestion failed')
      }
      const recipe = await res.json()
      setPreview(recipe)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleIngestImage = async () => {
    if (!files || files.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      for (const file of files) {
        formData.append('files', file)
      }
      const authHeaders = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/ingest/image`, {
        method: 'POST',
        headers: { ...authHeaders },
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Ingestion failed')
      }
      const recipe = await res.json()
      setPreview(recipe)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!preview) return
    setLoading(true)
    setError(null)

    const { is_vegetarian, error: _err, ...recipeData } = preview
    recipeData.user_id = user.id
    const { error: dbError } = await supabase.from('recipes').insert(recipeData)

    if (dbError) {
      setError(dbError.message)
      setLoading(false)
    } else {
      setLoading(false)
      onSaved()
    }
  }

  const handleDiscard = () => {
    setPreview(null)
    setUrl('')
    setFiles(null)
  }

  if (preview) {
    return (
      <div className="recipe-form">
        <h2>Review Recipe</h2>

        {preview.is_vegetarian === false && (
          <div className="warning">This recipe contains meat or fish and is NOT vegetarian.</div>
        )}

        <div className="preview-card">
          <h3>{preview.title}</h3>
          {preview.description && <p className="card-desc">{preview.description}</p>}

          <div className="card-meta">
            {preview.category && <span>{preview.category}</span>}
            {preview.servings && <span>{preview.servings} servings</span>}
            {preview.prep_time_minutes && <span>{preview.prep_time_minutes} min prep</span>}
            {preview.cook_time_minutes && <span>{preview.cook_time_minutes} min cook</span>}
            {preview.bake_time_minutes && <span>{preview.bake_time_minutes} min bake</span>}
          </div>

          {preview.tags?.length > 0 && (
            <div className="card-tags">
              {preview.tags.map(tag => <span key={tag} className="badge tag">{tag}</span>)}
            </div>
          )}

          {preview.ingredients?.length > 0 && (
            <div className="detail-section">
              <h4>Ingredients</h4>
              <ul>
                {preview.ingredients.map((ing, i) => (
                  <li key={i}>{ing.quantity} {ing.unit} {ing.name}</li>
                ))}
              </ul>
            </div>
          )}

          {preview.instructions?.length > 0 && (
            <div className="detail-section">
              <h4>Instructions</h4>
              <ol>
                {preview.instructions.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}
        </div>

        <div className="preview-actions">
          <button className="submit-btn" onClick={handleSave} disabled={loading}>
            {loading ? 'Saving...' : 'Save Recipe'}
          </button>
          <button className="discard-btn" onClick={handleDiscard}>
            Discard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="recipe-form">
      <h2>Import Recipe</h2>

      {error && <div className="error">{error}</div>}

      <div className="mode-tabs">
        <button className={mode === 'url' ? 'active' : ''} onClick={() => setMode('url')}>
          Web Link
        </button>
        <button className={mode === 'youtube' ? 'active' : ''} onClick={() => setMode('youtube')}>
          YouTube
        </button>
        <button className={mode === 'image' ? 'active' : ''} onClick={() => setMode('image')}>
          Photo
        </button>
      </div>

      {(mode === 'url' || mode === 'youtube') && (
        <div className="ingest-input">
          <label>
            {mode === 'url' ? 'Recipe URL' : 'YouTube Short URL'}
            <input
              type="url"
              placeholder={mode === 'url' ? 'https://example.com/recipe...' : 'https://youtube.com/shorts/...'}
              value={url}
              onChange={e => setUrl(e.target.value)}
            />
          </label>
          <button
            className="submit-btn"
            onClick={handleIngestUrl}
            disabled={loading || !url.trim()}
          >
            {loading ? 'Analyzing...' : 'Extract Recipe'}
          </button>
        </div>
      )}

      {mode === 'image' && (
        <div className="ingest-input">
          <label>
            Upload photo(s) of recipe
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={e => setFiles(e.target.files)}
            />
          </label>
          <button
            className="submit-btn"
            onClick={handleIngestImage}
            disabled={loading || !files?.length}
          >
            {loading ? 'Analyzing...' : 'Extract Recipe'}
          </button>
        </div>
      )}

      {loading && <p className="status">AI is reading the recipe... this may take a few seconds.</p>}
    </div>
  )
}

export default RecipeIngest
