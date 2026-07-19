### Task 3: Frontend — Update RecipeIngest component

**Files:**
- Modify: `frontend/src/components/RecipeIngest.jsx`
- Modify: `frontend/src/index.css` (add CSS for skip button and saved notice)

- [ ] **Step 1: Remove `handleSave` function**

Delete the `handleSave` function (lines 85-101 in current file).

- [ ] **Step 2: Update `handleDiscard` to delete from Supabase**

Replace `handleDiscard`:

```jsx
const handleDiscard = async () => {
  if (preview?.id) {
    setLoading(true)
    const { error } = await supabase.from('recipes').delete().eq('id', preview.id)
    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }
  }
  setPreview(null)
  setUrl('')
  setFiles(null)
  setLoading(false)
}
```

- [ ] **Step 3: Add `handleSkip` function**

Add after `handleDiscard`:

```jsx
const handleSkip = () => {
  onSaved()
}
```

- [ ] **Step 4: Update the preview render block**

Replace the entire preview section (lines 109-168):

```jsx
if (preview) {
  return (
    <div className="recipe-form">
      <h2>Review Recipe</h2>

      <div className="saved-notice">✓ Recipe saved</div>

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
        <button className="submit-btn" onClick={onSaved}>
          View in List
        </button>
        <button className="discard-btn" onClick={handleDiscard} disabled={loading}>
          {loading ? 'Deleting...' : 'Discard'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Add Skip button to loading state**

Find the loading indicator (line 238):

```jsx
{loading && <p className="status">AI is reading the recipe... this may take a few seconds.</p>}
```

Replace with:

```jsx
{loading && (
  <div>
    <p className="status">AI is reading the recipe... this may take a few seconds.</p>
    <div className="skip-area">
      <button className="skip-btn" onClick={handleSkip}>
        Skip & Save
      </button>
    </div>
  </div>
)}
```

- [ ] **Step 6: Add CSS for new elements**

Add to `frontend/src/index.css` (before the AI Consultation section at line 770):

```css
.skip-area {
  text-align: center;
  margin-top: -20px;
  margin-bottom: 12px;
}

.skip-btn {
  padding: 10px 24px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 0.9rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.skip-btn:hover {
  border-color: var(--green);
  color: var(--green);
}

.saved-notice {
  padding: 10px 12px;
  background: var(--green-bg);
  color: var(--green);
  border-radius: 8px;
  margin-bottom: 14px;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
}
```
