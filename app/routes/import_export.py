from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from io import StringIO, BytesIO
import csv
import json
import os
import tempfile
from app import db
from app.models import Recipe, Ingredient, Category, RecipeSection, SectionIngredient
from app.services.csv_handler import parse_recipe_csv, create_csv_export

bp = Blueprint('import_export', __name__)


def get_preview_file_path():
    """Get the path for storing preview data."""
    # Use a session-specific temp file
    session_id = session.get('_import_session_id')
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        session['_import_session_id'] = session_id

    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f'cookbook_import_{session_id}.json')


def save_preview_data(recipes, errors):
    """Save preview data to a temp file."""
    file_path = get_preview_file_path()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({'recipes': recipes, 'errors': errors}, f)


def load_preview_data():
    """Load preview data from temp file."""
    file_path = get_preview_file_path()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('recipes', []), data.get('errors', [])
    return [], []


def clear_preview_data():
    """Clear the preview temp file."""
    file_path = get_preview_file_path()
    if os.path.exists(file_path):
        os.remove(file_path)


@bp.route('/')
def index():
    """Import page."""
    return render_template('import/upload.html')


@bp.route('/template')
def download_template():
    """Download CSV template."""
    template_content = """title,category,description,prep_time_minutes,cook_time_minutes,rest_time_minutes,servings,servings_unit,ingredients,instructions,notes,source
"Chocolate Chip Cookies","Desserts","Classic homemade chocolate chip cookies",15,12,30,24,cookies,"2 cups all-purpose flour|1 cup butter, softened|3/4 cup granulated sugar|3/4 cup brown sugar, packed|2 large eggs|1 tsp vanilla extract|1 tsp baking soda|1/2 tsp salt|2 cups chocolate chips","1. Preheat oven to 375°F (190°C).
2. In a large bowl, cream together butter and sugars until fluffy.
3. Beat in eggs one at a time, then add vanilla.
4. In a separate bowl, whisk flour, baking soda, and salt.
5. Gradually blend dry ingredients into the butter mixture.
6. Fold in chocolate chips.
7. Drop rounded tablespoons onto ungreased baking sheets.
8. Bake 9-11 minutes or until golden brown.
9. Cool on baking sheet for 2 minutes before transferring to wire rack.","Let dough chill for 30 minutes for thicker cookies.","Family recipe"
"Simple Garden Salad","Soups & Salads","Fresh and simple side salad",10,0,,4,servings,"1 head romaine lettuce, chopped|1 cup cherry tomatoes, halved|1 cucumber, sliced|1/4 red onion, thinly sliced|1/4 cup olive oil|2 tbsp red wine vinegar|salt and pepper to taste","1. Wash and dry all vegetables.
2. Combine lettuce, tomatoes, cucumber, and onion in a large bowl.
3. Whisk together olive oil and vinegar.
4. Drizzle dressing over salad just before serving.
5. Season with salt and pepper to taste.","Add croutons or cheese for extra flavor.",""
"""
    buffer = BytesIO(template_content.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='cookbook_import_template.csv'
    )


@bp.route('/upload', methods=['POST'])
def upload():
    """Process uploaded CSV file."""
    if 'file' not in request.files:
        flash('No file uploaded.', 'error')
        return redirect(url_for('import_export.index'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('import_export.index'))

    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file.', 'error')
        return redirect(url_for('import_export.index'))

    try:
        content = file.read().decode('utf-8')
        recipes, errors = parse_recipe_csv(content)

        if errors and not recipes:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('import_export.index'))

        # Store in temp file for preview (session cookies have size limits)
        save_preview_data(recipes, errors)

        return render_template(
            'import/preview.html',
            recipes=recipes,
            errors=errors
        )

    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('import_export.index'))


@bp.route('/confirm', methods=['POST'])
def confirm_import():
    """Confirm and process the import."""
    recipes, errors = load_preview_data()
    if not recipes:
        flash('No recipes to import.', 'error')
        return redirect(url_for('import_export.index'))

    imported_count = 0
    try:
        for recipe_data in recipes:
            # Get or create category
            category = None
            if recipe_data.get('category'):
                category = Category.query.filter_by(name=recipe_data['category']).first()
                if not category:
                    category = Category(
                        name=recipe_data['category'],
                        sort_order=Category.query.count() + 1
                    )
                    db.session.add(category)
                    db.session.flush()

            has_sections = recipe_data.get('has_sections', False)

            # Create recipe
            recipe = Recipe(
                title=recipe_data['title'],
                description=recipe_data.get('description'),
                category_id=category.id if category else None,
                prep_time_minutes=recipe_data.get('prep_time_minutes'),
                cook_time_minutes=recipe_data.get('cook_time_minutes'),
                rest_time_minutes=recipe_data.get('rest_time_minutes'),
                servings=recipe_data.get('servings'),
                servings_unit=recipe_data.get('servings_unit', 'servings'),
                instructions=recipe_data.get('instructions') if not has_sections else None,
                has_sections=has_sections,
                notes=recipe_data.get('notes'),
                source=recipe_data.get('source')
            )
            db.session.add(recipe)
            db.session.flush()

            if has_sections:
                # Add sections with their ingredients
                for section_order, section_data in enumerate(recipe_data.get('sections', [])):
                    section = RecipeSection(
                        recipe_id=recipe.id,
                        name=section_data['name'],
                        instructions=section_data['instructions'],
                        sort_order=section_order
                    )
                    db.session.add(section)
                    db.session.flush()

                    for ing_order, ing_data in enumerate(section_data.get('ingredients', [])):
                        ingredient = SectionIngredient(
                            section_id=section.id,
                            name=ing_data['name'],
                            quantity=ing_data.get('quantity'),
                            unit=ing_data.get('unit'),
                            preparation=ing_data.get('preparation'),
                            is_optional=ing_data.get('is_optional', False),
                            sort_order=ing_order
                        )
                        db.session.add(ingredient)
            else:
                # Add simple ingredients
                for i, ing_data in enumerate(recipe_data.get('ingredients', [])):
                    ingredient = Ingredient(
                        recipe_id=recipe.id,
                        name=ing_data['name'],
                        quantity=ing_data.get('quantity'),
                        unit=ing_data.get('unit'),
                        preparation=ing_data.get('preparation'),
                        is_optional=ing_data.get('is_optional', False),
                        sort_order=i
                    )
                    db.session.add(ingredient)

            imported_count += 1

        db.session.commit()

        # Clear temp file
        clear_preview_data()

        flash(f'Successfully imported {imported_count} recipes.', 'success')
        return redirect(url_for('recipes.index'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error importing recipes: {str(e)}', 'error')
        return redirect(url_for('import_export.index'))


@bp.route('/export')
def export():
    """Export all recipes as CSV."""
    recipes = Recipe.query.all()
    csv_content = create_csv_export(recipes)

    buffer = BytesIO(csv_content.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='cookbook_export.csv'
    )
