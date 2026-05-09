import { useState } from 'react'

function RecipeCard({ recipe, onDelete }) {
  const [expanded, setExpanded] = useState(false)

  const totalTime = [
    recipe.prep_time_minutes,
    recipe.cook_time_minutes,
    recipe.bake_time_minutes,
  ].filter(Boolean).reduce((a, b) => a + b, 0)

  return (
    <div className="recipe-card" onClick={() => setExpanded(!expanded)}>
      <div className="card-header">
        <h3>{recipe.title}</h3>
        {recipe.category && <span className="badge category">{recipe.category}</span>}
      </div>

      {recipe.description && <p className="card-desc">{recipe.description}</p>}

      <div className="card-meta">
        {totalTime > 0 && <span>{totalTime} min</span>}
        {recipe.servings && <span>{recipe.servings} servings</span>}
        {recipe.rating && <span>{'★'.repeat(recipe.rating)}{'☆'.repeat(5 - recipe.rating)}</span>}
      </div>

      {recipe.tags?.length > 0 && (
        <div className="card-tags">
          {recipe.tags.map(tag => <span key={tag} className="badge tag">{tag}</span>)}
        </div>
      )}

      {expanded && (
        <div className="card-details">
          {recipe.ingredients?.length > 0 && (
            <div className="detail-section">
              <h4>Ingredients</h4>
              <ul>
                {recipe.ingredients.map((ing, i) => (
                  <li key={i}>
                    {ing.quantity} {ing.unit} {ing.name}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {recipe.instructions?.length > 0 && (
            <div className="detail-section">
              <h4>Instructions</h4>
              <ol>
                {recipe.instructions.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          <button
            className="delete-btn"
            onClick={(e) => {
              e.stopPropagation()
              if (confirm('Delete this recipe?')) onDelete(recipe.id)
            }}
          >
            Delete Recipe
          </button>
        </div>
      )}
    </div>
  )
}

export default RecipeCard
