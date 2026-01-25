from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Category

bp = Blueprint('categories', __name__)


@bp.route('/')
def index():
    """List all categories."""
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('categories/index.html', categories=categories)


@bp.route('/new', methods=['GET', 'POST'])
def new():
    """Create a new category."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Category name is required.', 'error')
            return redirect(request.url)

        # Check for duplicate
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash('A category with this name already exists.', 'error')
            return redirect(request.url)

        description = request.form.get('description', '').strip()
        sort_order = request.form.get('sort_order', type=int) or 0

        category = Category(
            name=name,
            description=description or None,
            sort_order=sort_order
        )
        db.session.add(category)
        db.session.commit()

        flash(f'Category "{name}" has been created.', 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/form.html', category=None)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit a category."""
    category = Category.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Category name is required.', 'error')
            return redirect(request.url)

        # Check for duplicate (excluding current)
        existing = Category.query.filter(
            Category.name == name,
            Category.id != id
        ).first()
        if existing:
            flash('A category with this name already exists.', 'error')
            return redirect(request.url)

        category.name = name
        category.description = request.form.get('description', '').strip() or None
        category.sort_order = request.form.get('sort_order', type=int) or 0

        db.session.commit()
        flash(f'Category "{name}" has been updated.', 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/form.html', category=category)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete a category."""
    category = Category.query.get_or_404(id)

    # Check if category has recipes
    if category.recipe_count > 0:
        flash(f'Cannot delete "{category.name}" - it has {category.recipe_count} recipes.', 'error')
        return redirect(url_for('categories.index'))

    name = category.name
    db.session.delete(category)
    db.session.commit()

    flash(f'Category "{name}" has been deleted.', 'success')
    return redirect(url_for('categories.index'))


@bp.route('/api')
def api_list():
    """Return categories as JSON."""
    categories = Category.query.order_by(Category.sort_order).all()
    return jsonify([c.to_dict() for c in categories])
