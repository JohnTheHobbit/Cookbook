from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Recipe, Ingredient, Category

bp = Blueprint('recipes', __name__)


@bp.route('/')
def index():
    """List all recipes with optional filtering."""
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    favorites_only = request.args.get('favorites', '').lower() == 'true'
    sort_by = request.args.get('sort', 'updated')

    # Build query
    query = Recipe.query

    if category_id:
        query = query.filter_by(category_id=category_id)

    if favorites_only:
        query = query.filter_by(is_favorite=True)

    # Apply sorting
    if sort_by == 'title':
        query = query.order_by(Recipe.title)
    elif sort_by == 'created':
        query = query.order_by(Recipe.created_at.desc())
    else:  # default: updated
        query = query.order_by(Recipe.updated_at.desc())

    recipes = query.all()

    # Get categories for filter
    categories = Category.query.order_by(Category.sort_order).all()

    # Get current category name
    current_category = None
    if category_id:
        current_category = Category.query.get(category_id)

    # Check if htmx request
    if request.headers.get('HX-Request'):
        return render_template('components/recipe_cards.html', recipes=recipes)

    return render_template(
        'recipes/index.html',
        recipes=recipes,
        categories=categories,
        current_category=current_category,
        favorites_only=favorites_only,
        sort_by=sort_by
    )


@bp.route('/new', methods=['GET', 'POST'])
def new():
    """Create a new recipe."""
    if request.method == 'POST':
        return save_recipe(None)

    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('recipes/form.html', recipe=None, categories=categories)


@bp.route('/<int:id>')
def show(id):
    """Show a single recipe."""
    recipe = Recipe.query.get_or_404(id)
    return render_template('recipes/detail.html', recipe=recipe)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit a recipe."""
    recipe = Recipe.query.get_or_404(id)

    if request.method == 'POST':
        return save_recipe(recipe)

    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('recipes/form.html', recipe=recipe, categories=categories)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete a recipe."""
    recipe = Recipe.query.get_or_404(id)
    db.session.delete(recipe)
    db.session.commit()
    flash(f'Recipe "{recipe.title}" has been deleted.', 'success')
    return redirect(url_for('recipes.index'))


@bp.route('/<int:id>/favorite', methods=['POST'])
def toggle_favorite(id):
    """Toggle favorite status."""
    recipe = Recipe.query.get_or_404(id)
    recipe.is_favorite = not recipe.is_favorite
    db.session.commit()

    # Return JSON for htmx
    if request.headers.get('HX-Request'):
        return render_template('components/favorite_button.html', recipe=recipe)

    return jsonify({'is_favorite': recipe.is_favorite})


@bp.route('/<int:id>/print')
def print_view(id):
    """Print-friendly recipe view."""
    recipe = Recipe.query.get_or_404(id)
    return render_template('recipes/print.html', recipe=recipe)


def save_recipe(recipe):
    """Save a new or existing recipe from form data."""
    try:
        # Get form data
        title = request.form.get('title', '').strip()
        if not title:
            flash('Title is required.', 'error')
            return redirect(request.url)

        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', type=int)
        prep_time = request.form.get('prep_time_minutes', type=int)
        cook_time = request.form.get('cook_time_minutes', type=int)
        servings = request.form.get('servings', type=int)
        servings_unit = request.form.get('servings_unit', 'servings').strip()
        instructions = request.form.get('instructions', '').strip()
        notes = request.form.get('notes', '').strip()
        source = request.form.get('source', '').strip()

        if not instructions:
            flash('Instructions are required.', 'error')
            return redirect(request.url)

        # Create or update recipe
        if recipe is None:
            recipe = Recipe()
            db.session.add(recipe)

        recipe.title = title
        recipe.description = description or None
        recipe.category_id = category_id if category_id else None
        recipe.prep_time_minutes = prep_time
        recipe.cook_time_minutes = cook_time
        recipe.servings = servings
        recipe.servings_unit = servings_unit
        recipe.instructions = instructions
        recipe.notes = notes or None
        recipe.source = source or None

        # Handle ingredients
        # First, remove existing ingredients
        Ingredient.query.filter_by(recipe_id=recipe.id).delete()

        # Add new ingredients
        ingredient_names = request.form.getlist('ingredient_name[]')
        ingredient_quantities = request.form.getlist('ingredient_quantity[]')
        ingredient_units = request.form.getlist('ingredient_unit[]')
        ingredient_preps = request.form.getlist('ingredient_preparation[]')
        ingredient_optionals = request.form.getlist('ingredient_optional[]')

        for i, name in enumerate(ingredient_names):
            if not name.strip():
                continue

            quantity_str = ingredient_quantities[i] if i < len(ingredient_quantities) else ''
            quantity = parse_quantity(quantity_str) if quantity_str.strip() else None

            ingredient = Ingredient(
                recipe=recipe,
                name=name.strip(),
                quantity=quantity,
                unit=ingredient_units[i].strip() if i < len(ingredient_units) else None,
                preparation=ingredient_preps[i].strip() if i < len(ingredient_preps) else None,
                is_optional=str(i) in ingredient_optionals,
                sort_order=i
            )
            db.session.add(ingredient)

        db.session.commit()
        flash(f'Recipe "{recipe.title}" has been saved.', 'success')
        return redirect(url_for('recipes.show', id=recipe.id))

    except Exception as e:
        db.session.rollback()
        flash(f'Error saving recipe: {str(e)}', 'error')
        return redirect(request.url)


def parse_quantity(value):
    """Parse a quantity string to a float."""
    if not value:
        return None

    value = value.strip()

    # Handle fractions
    fraction_map = {
        '1/4': 0.25,
        '1/3': 0.33,
        '1/2': 0.5,
        '2/3': 0.67,
        '3/4': 0.75,
    }

    # Check for mixed number (e.g., "1 1/2")
    parts = value.split()
    if len(parts) == 2:
        try:
            whole = float(parts[0])
            fraction = fraction_map.get(parts[1], 0)
            return whole + fraction
        except ValueError:
            pass

    # Check for simple fraction
    if value in fraction_map:
        return fraction_map[value]

    # Try parsing as float
    try:
        return float(value)
    except ValueError:
        return None
