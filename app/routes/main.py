from flask import Blueprint, render_template, request
from app.models import Recipe, Category
from sqlalchemy import or_

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Home page - shows recent recipes and search."""
    # Get recent recipes
    recent_recipes = Recipe.query.order_by(Recipe.updated_at.desc()).limit(6).all()

    # Get favorite recipes
    favorite_recipes = Recipe.query.filter_by(is_favorite=True).order_by(
        Recipe.updated_at.desc()
    ).limit(6).all()

    # Get categories with counts
    categories = Category.query.order_by(Category.sort_order).all()

    # Get total counts
    total_recipes = Recipe.query.count()
    total_favorites = Recipe.query.filter_by(is_favorite=True).count()

    return render_template(
        'index.html',
        recent_recipes=recent_recipes,
        favorite_recipes=favorite_recipes,
        categories=categories,
        total_recipes=total_recipes,
        total_favorites=total_favorites
    )


@bp.route('/search')
def search():
    """Search recipes."""
    query = request.args.get('q', '').strip()

    if not query:
        return render_template('search_results.html', recipes=[], query='')

    # Search in title, description, instructions, and notes
    search_term = f'%{query}%'
    recipes = Recipe.query.filter(
        or_(
            Recipe.title.ilike(search_term),
            Recipe.description.ilike(search_term),
            Recipe.instructions.ilike(search_term),
            Recipe.notes.ilike(search_term)
        )
    ).order_by(Recipe.title).all()

    # Check if this is an htmx request
    if request.headers.get('HX-Request'):
        return render_template('components/recipe_cards.html', recipes=recipes)

    return render_template('search_results.html', recipes=recipes, query=query)
