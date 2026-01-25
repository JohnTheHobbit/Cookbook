from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from io import StringIO, BytesIO
import csv
from app import db
from app.models import Recipe, Ingredient, Category
from app.services.csv_handler import parse_recipe_csv, create_csv_export

bp = Blueprint('import_export', __name__)


@bp.route('/')
def index():
    """Import page."""
    return render_template('import/upload.html')


@bp.route('/template')
def download_template():
    """Download CSV template."""
    template_content = """title,category,description,prep_time_minutes,cook_time_minutes,servings,servings_unit,ingredients,instructions,notes,source
"Chocolate Chip Cookies","Desserts","Classic homemade chocolate chip cookies",15,12,24,cookies,"2 cups all-purpose flour|1 cup butter, softened|3/4 cup granulated sugar|3/4 cup brown sugar, packed|2 large eggs|1 tsp vanilla extract|1 tsp baking soda|1/2 tsp salt|2 cups chocolate chips","1. Preheat oven to 375°F (190°C).
2. In a large bowl, cream together butter and sugars until fluffy.
3. Beat in eggs one at a time, then add vanilla.
4. In a separate bowl, whisk flour, baking soda, and salt.
5. Gradually blend dry ingredients into the butter mixture.
6. Fold in chocolate chips.
7. Drop rounded tablespoons onto ungreased baking sheets.
8. Bake 9-11 minutes or until golden brown.
9. Cool on baking sheet for 2 minutes before transferring to wire rack.","Let dough chill for 30 minutes for thicker cookies.","Family recipe"
"Simple Garden Salad","Soups & Salads","Fresh and simple side salad",10,0,4,servings,"1 head romaine lettuce, chopped|1 cup cherry tomatoes, halved|1 cucumber, sliced|1/4 red onion, thinly sliced|1/4 cup olive oil|2 tbsp red wine vinegar|salt and pepper to taste","1. Wash and dry all vegetables.
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

        # Store in session for preview
        from flask import session
        session['import_preview'] = recipes
        session['import_errors'] = errors

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
    from flask import session

    recipes = session.get('import_preview', [])
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

            # Create recipe
            recipe = Recipe(
                title=recipe_data['title'],
                description=recipe_data.get('description'),
                category_id=category.id if category else None,
                prep_time_minutes=recipe_data.get('prep_time_minutes'),
                cook_time_minutes=recipe_data.get('cook_time_minutes'),
                servings=recipe_data.get('servings'),
                servings_unit=recipe_data.get('servings_unit', 'servings'),
                instructions=recipe_data['instructions'],
                notes=recipe_data.get('notes'),
                source=recipe_data.get('source')
            )
            db.session.add(recipe)
            db.session.flush()

            # Add ingredients
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

        # Clear session
        session.pop('import_preview', None)
        session.pop('import_errors', None)

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
