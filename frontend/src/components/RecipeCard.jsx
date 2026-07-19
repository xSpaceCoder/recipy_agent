import { useState } from 'react'

function RecipeCard({ recipe, onDelete, onEdit, isOwner }) {
  const [expanded, setExpanded] = useState(false)

  const totalTime = [
    recipe.prep_time_minutes,
    recipe.cook_time_minutes,
    recipe.bake_time_minutes,
  ].filter(Boolean).reduce((a, b) => a + b, 0)

  return (
    <div className="recipe-card" onClick={() => setExpanded(!expanded)}>
      <div className="card-main">
        <div className="card-image">
          {recipe.image_url ? (
            <img src={recipe.image_url} alt={recipe.title} />
          ) : (
            <div className="card-image-placeholder">
              <span>{recipe.category === 'cake' || recipe.category === 'dessert' ? '🍰' : '🍽️'}</span>
            </div>
          )}
        </div>
        <div className="card-body">
          <div className="card-header">
            <h3>{recipe.title}</h3>
            {recipe.category && <span className="badge category">{recipe.category}</span>}
          </div>

          {recipe.ai_explanation && (
            <p className="ai-explanation">{recipe.ai_explanation}</p>
          )}

          {recipe.description && <p className="card-desc">{recipe.description}</p>}

          <div className="card-meta">
            {totalTime > 0 && <span>{totalTime} min</span>}
            {recipe.servings && <span>{recipe.servings} servings</span>}
            {isOwner && recipe.rating && <span>{'★'.repeat(recipe.rating)}{'☆'.repeat(5 - recipe.rating)}</span>}
          </div>

          {recipe.tags?.length > 0 && (
            <div className="card-tags">
              {recipe.tags.map(tag => <span key={tag} className="badge tag">{tag}</span>)}
            </div>
          )}
        </div>
      </div>

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

          {(recipe.source_url || recipe.source_image_urls?.length > 0) && (
            <div className="detail-section source-section">
              <h4>Source</h4>
              {recipe.source_url && (
                <p>
                  <a href={recipe.source_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}>
                    {recipe.source_type === 'video' ? 'YouTube Video' : 'Original Link'}
                  </a>
                  {recipe.source_accessed_at && (
                    <span className="source-date">
                      {' '}— accessed {new Date(recipe.source_accessed_at).toLocaleDateString()}
                    </span>
                  )}
                </p>
              )}
              {recipe.source_image_urls?.length > 0 && (
                <div className="source-images">
                  {recipe.source_image_urls.map((url, i) => (
                    <img key={i} src={url} alt={`Source photo ${i + 1}`} className="source-image" onClick={e => e.stopPropagation()} />
                  ))}
                  {recipe.source_accessed_at && !recipe.source_url && (
                    <p className="source-date">
                      Added {new Date(recipe.source_accessed_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {isOwner && (
            <div className="card-actions">
              <button
                className="edit-btn"
                onClick={(e) => {
                  e.stopPropagation()
                  onEdit(recipe)
                }}
              >
                Edit Recipe
              </button>
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
      )}
    </div>
  )
}

export default RecipeCard
