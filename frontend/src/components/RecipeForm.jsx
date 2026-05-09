import { useState } from 'react'
import { supabase } from '../lib/supabase'

const CATEGORIES = ['dinner', 'cake', 'dessert', 'soup/stew', 'breakfast', 'snack']
const SEASONS = ['spring', 'summer', 'autumn', 'winter', 'all']
const COMMON_TAGS = ['vegetarian', 'vegan', 'gluten-free', 'light', 'cozy', 'fiber-rich', 'quick', 'meal-prep']

function RecipeForm({ onSaved }) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({
    title: '',
    description: '',
    servings: '',
    prep_time_minutes: '',
    cook_time_minutes: '',
    bake_time_minutes: '',
    category: '',
    season: ['all'],
    tags: [],
    ingredients: [{ name: '', quantity: '', unit: '' }],
    instructions: [''],
  })

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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)

    const recipe = {
      title: form.title.trim(),
      description: form.description.trim() || null,
      servings: form.servings ? parseInt(form.servings) : null,
      prep_time_minutes: form.prep_time_minutes ? parseInt(form.prep_time_minutes) : null,
      cook_time_minutes: form.cook_time_minutes ? parseInt(form.cook_time_minutes) : null,
      bake_time_minutes: form.bake_time_minutes ? parseInt(form.bake_time_minutes) : null,
      category: form.category || null,
      season: form.season,
      tags: form.tags,
      ingredients: form.ingredients.filter(i => i.name.trim()),
      instructions: form.instructions.filter(i => i.trim()),
      source_type: 'manual',
    }

    const { error: err } = await supabase.from('recipes').insert(recipe)

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
      <h2>Add Recipe</h2>

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

      <label>
        Category
        <select value={form.category} onChange={e => updateField('category', e.target.value)}>
          <option value="">Select...</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </label>

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
        </div>
      </fieldset>

      <fieldset>
        <legend>Ingredients</legend>
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
        <legend>Instructions</legend>
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
        {saving ? 'Saving...' : 'Save Recipe'}
      </button>
    </form>
  )
}

export default RecipeForm
