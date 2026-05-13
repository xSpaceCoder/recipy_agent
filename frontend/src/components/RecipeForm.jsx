import { useState } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../lib/useAuth'

const CATEGORIES = ['dinner', 'cake', 'dessert', 'soup/stew', 'breakfast', 'snack']
const SEASONS = ['spring', 'summer', 'autumn', 'winter', 'all']
const COMMON_TAGS = ['vegetarian', 'vegan', 'gluten-free', 'light', 'cozy', 'fiber-rich', 'quick', 'meal-prep']
const SOURCE_TYPES = ['manual', 'link', 'video', 'image']

function RecipeForm({ onSaved, recipe }) {
  const { user } = useAuth()
  const isEdit = Boolean(recipe)

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const isOwner = !isEdit || recipe?.user_id === user?.id

  const [form, setForm] = useState({
    title: recipe?.title || '',
    description: recipe?.description || '',
    servings: recipe?.servings?.toString() || '',
    prep_time_minutes: recipe?.prep_time_minutes?.toString() || '',
    cook_time_minutes: recipe?.cook_time_minutes?.toString() || '',
    bake_time_minutes: recipe?.bake_time_minutes?.toString() || '',
    chill_time_minutes: recipe?.chill_time_minutes?.toString() || '',
    freeze_time_minutes: recipe?.freeze_time_minutes?.toString() || '',
    category: recipe?.category || '',
    season: recipe?.season || ['all'],
    tags: recipe?.tags || [],
    rating: recipe?.rating?.toString() || '',
    visibility: recipe?.visibility || 'public',
    source_url: recipe?.source_url || '',
    source_type: recipe?.source_type || 'manual',
    ingredients: recipe?.ingredients?.length > 0
      ? recipe.ingredients
      : [{ name: '', quantity: '', unit: '' }],
    instructions: recipe?.instructions?.length > 0
      ? recipe.instructions
      : [''],
  })
  const [customTag, setCustomTag] = useState('')

  const updateField = (field, value) => {
    setForm(f => ({ ...f, [field]: value }))
  }

  const toggleTag = (tag) => {
    setForm(f => ({
      ...f,
      tags: f.tags.includes(tag)
        ? f.tags.filter(t => t !== tag)
        : [...f.tags, tag]
    }))
  }

  const addCustomTag = () => {
    const tag = customTag.trim().toLowerCase()
    if (tag && !form.tags.includes(tag)) {
      setForm(f => ({ ...f, tags: [...f.tags, tag] }))
    }
    setCustomTag('')
  }

  const toggleSeason = (s) => {
    setForm(f => {
      const current = f.season
      if (s === 'all') return { ...f, season: ['all'] }
      const without = current.filter(x => x !== 'all' && x !== s)
      const next = current.includes(s) ? without : [...without, s]
      return { ...f, season: next.length === 0 ? ['all'] : next }
    })
  }

  const updateIngredient = (index, field, value) => {
    setForm(f => {
      const ingredients = [...f.ingredients]
      ingredients[index] = { ...ingredients[index], [field]: value }
      return { ...f, ingredients }
    })
  }

  const addIngredient = () => {
    setForm(f => ({ ...f, ingredients: [...f.ingredients, { name: '', quantity: '', unit: '' }] }))
  }

  const removeIngredient = (index) => {
    setForm(f => ({ ...f, ingredients: f.ingredients.filter((_, i) => i !== index) }))
  }

  const updateInstruction = (index, value) => {
    setForm(f => {
      const instructions = [...f.instructions]
      instructions[index] = value
      return { ...f, instructions }
    })
  }

  const addInstruction = () => {
    setForm(f => ({ ...f, instructions: [...f.instructions, ''] }))
  }

  const removeInstruction = (index) => {
    setForm(f => ({ ...f, instructions: f.instructions.filter((_, i) => i !== index) }))
  }

  const validate = () => {
    if (!form.title.trim()) return 'Title is required.'
    if (form.servings && (parseInt(form.servings) < 1 || isNaN(parseInt(form.servings)))) {
      return 'Servings must be a positive number.'
    }
    if (form.rating && (parseInt(form.rating) < 1 || parseInt(form.rating) > 5)) {
      return 'Rating must be between 1 and 5.'
    }
    const timeFields = ['prep_time_minutes', 'cook_time_minutes', 'bake_time_minutes', 'chill_time_minutes', 'freeze_time_minutes']
    for (const field of timeFields) {
      if (form[field] && (parseInt(form[field]) < 0 || isNaN(parseInt(form[field])))) {
        return `${field.replace(/_/g, ' ').replace(' minutes', '')} must be a non-negative number.`
      }
    }
    if (form.source_url && form.source_type === 'manual') {
      return 'If you add a source URL, please also select the source type (link or video).'
    }
    if (form.source_url && !isValidUrl(form.source_url)) {
      return 'Source URL must be a valid URL (starting with http:// or https://).'
    }
    const validIngredients = form.ingredients.filter(i => i.name.trim())
    if (validIngredients.length === 0) return 'Add at least one ingredient.'
    const validInstructions = form.instructions.filter(i => i.trim())
    if (validInstructions.length === 0) return 'Add at least one instruction step.'
    return null
  }

  const isValidUrl = (str) => {
    try {
      const url = new URL(str)
      return url.protocol === 'http:' || url.protocol === 'https:'
    } catch {
      return false
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    setSaving(true)
    setError(null)

    const recipeData = {
      title: form.title.trim(),
      description: form.description.trim() || null,
      servings: form.servings ? parseInt(form.servings) : null,
      prep_time_minutes: form.prep_time_minutes ? parseInt(form.prep_time_minutes) : null,
      cook_time_minutes: form.cook_time_minutes ? parseInt(form.cook_time_minutes) : null,
      bake_time_minutes: form.bake_time_minutes ? parseInt(form.bake_time_minutes) : null,
      chill_time_minutes: form.chill_time_minutes ? parseInt(form.chill_time_minutes) : null,
      freeze_time_minutes: form.freeze_time_minutes ? parseInt(form.freeze_time_minutes) : null,
      category: form.category || null,
      season: form.season,
      tags: form.tags,
      rating: form.rating ? parseInt(form.rating) : null,
      visibility: form.visibility,
      source_url: form.source_url.trim() || null,
      source_type: form.source_type,
      ingredients: form.ingredients.filter(i => i.name.trim()),
      instructions: form.instructions.filter(i => i.trim()),
    }

    let err
    if (isEdit) {
      const { error: updateErr } = await supabase
        .from('recipes')
        .update(recipeData)
        .eq('id', recipe.id)
      err = updateErr
    } else {
      recipeData.user_id = user.id
      const { error: insertErr } = await supabase
        .from('recipes')
        .insert(recipeData)
      err = insertErr
    }

    if (err) {
      setError(err.message)
      setSaving(false)
    } else {
      setSaving(false)
      onSaved()
    }
  }

  return (
    <form className="recipe-form" onSubmit={handleSubmit}>
      <h2>{isEdit ? 'Edit Recipe' : 'Add Recipe'}</h2>

      {error && <div className="error">{error}</div>}

      <label>
        Title *
        <input
          type="text"
          required
          value={form.title}
          onChange={e => updateField('title', e.target.value)}
          placeholder="e.g. Mushroom Risotto"
        />
      </label>

      <label>
        Description
        <textarea
          value={form.description}
          onChange={e => updateField('description', e.target.value)}
          placeholder="Brief description of the dish"
          rows={2}
        />
      </label>

      <div className="row">
        <label>
          Servings
          <input type="number" min="1" value={form.servings} onChange={e => updateField('servings', e.target.value)} />
        </label>
        <label>
          Prep (min)
          <input type="number" min="0" value={form.prep_time_minutes} onChange={e => updateField('prep_time_minutes', e.target.value)} />
        </label>
        <label>
          Cook (min)
          <input type="number" min="0" value={form.cook_time_minutes} onChange={e => updateField('cook_time_minutes', e.target.value)} />
        </label>
        <label>
          Bake (min)
          <input type="number" min="0" value={form.bake_time_minutes} onChange={e => updateField('bake_time_minutes', e.target.value)} />
        </label>
      </div>

      <div className="row">
        <label>
          Chill (min)
          <input type="number" min="0" value={form.chill_time_minutes} onChange={e => updateField('chill_time_minutes', e.target.value)} />
        </label>
        <label>
          Freeze (min)
          <input type="number" min="0" value={form.freeze_time_minutes} onChange={e => updateField('freeze_time_minutes', e.target.value)} />
        </label>
        {isOwner && (
          <label>
            Rating (1-5)
            <input type="number" min="1" max="5" value={form.rating} onChange={e => updateField('rating', e.target.value)} />
          </label>
        )}
        <label>
          Category
          <select value={form.category} onChange={e => updateField('category', e.target.value)}>
            <option value="">Select...</option>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
      </div>

      <fieldset>
        <legend>Source</legend>
        <div className="row">
          <label>
            Source Type
            <select value={form.source_type} onChange={e => updateField('source_type', e.target.value)}>
              {SOURCE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>
          <label style={{ gridColumn: 'span 3' }}>
            Source URL
            <input
              type="url"
              value={form.source_url}
              onChange={e => updateField('source_url', e.target.value)}
              placeholder="https://..."
            />
          </label>
        </div>
      </fieldset>

      {isOwner && (
        <fieldset>
          <legend>Visibility</legend>
          <div className="chip-group">
            <button
              type="button"
              className={`chip ${form.visibility === 'public' ? 'selected' : ''}`}
              onClick={() => updateField('visibility', 'public')}
            >
              Public
            </button>
            <button
              type="button"
              className={`chip ${form.visibility === 'private' ? 'selected' : ''}`}
              onClick={() => updateField('visibility', 'private')}
            >
              Private
            </button>
          </div>
        </fieldset>
      )}

      <fieldset>
        <legend>Season</legend>
        <div className="chip-group">
          {SEASONS.map(s => (
            <button
              type="button"
              key={s}
              className={`chip ${form.season.includes(s) ? 'selected' : ''}`}
              onClick={() => toggleSeason(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend>Tags</legend>
        <div className="chip-group">
          {COMMON_TAGS.map(tag => (
            <button
              type="button"
              key={tag}
              className={`chip ${form.tags.includes(tag) ? 'selected' : ''}`}
              onClick={() => toggleTag(tag)}
            >
              {tag}
            </button>
          ))}
          {form.tags.filter(t => !COMMON_TAGS.includes(t)).map(tag => (
            <button
              type="button"
              key={tag}
              className="chip selected"
              onClick={() => toggleTag(tag)}
            >
              {tag}
            </button>
          ))}
        </div>
        <div className="custom-tag-row">
          <input
            type="text"
            placeholder="Add custom tag..."
            value={customTag}
            onChange={e => setCustomTag(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addCustomTag() } }}
          />
          <button type="button" className="add-btn" onClick={addCustomTag}>+</button>
        </div>
      </fieldset>

      <fieldset>
        <legend>Ingredients *</legend>
        {form.ingredients.map((ing, i) => (
          <div key={i} className="ingredient-row">
            <input
              placeholder="Ingredient"
              value={ing.name}
              onChange={e => updateIngredient(i, 'name', e.target.value)}
            />
            <input
              placeholder="Qty"
              value={ing.quantity}
              onChange={e => updateIngredient(i, 'quantity', e.target.value)}
              className="small"
            />
            <input
              placeholder="Unit"
              value={ing.unit}
              onChange={e => updateIngredient(i, 'unit', e.target.value)}
              className="small"
            />
            {form.ingredients.length > 1 && (
              <button type="button" className="remove-btn" onClick={() => removeIngredient(i)}>x</button>
            )}
          </div>
        ))}
        <button type="button" className="add-btn" onClick={addIngredient}>+ Ingredient</button>
      </fieldset>

      <fieldset>
        <legend>Instructions *</legend>
        {form.instructions.map((step, i) => (
          <div key={i} className="instruction-row">
            <span className="step-num">{i + 1}.</span>
            <textarea
              value={step}
              onChange={e => updateInstruction(i, e.target.value)}
              placeholder={`Step ${i + 1}`}
              rows={2}
            />
            {form.instructions.length > 1 && (
              <button type="button" className="remove-btn" onClick={() => removeInstruction(i)}>x</button>
            )}
          </div>
        ))}
        <button type="button" className="add-btn" onClick={addInstruction}>+ Step</button>
      </fieldset>

      <button type="submit" className="submit-btn" disabled={saving}>
        {saving ? 'Saving...' : isEdit ? 'Update Recipe' : 'Save Recipe'}
      </button>
    </form>
  )
}

export default RecipeForm
