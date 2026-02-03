import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from app.config import config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    """Application factory."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.recipes import bp as recipes_bp
    from app.routes.categories import bp as categories_bp
    from app.routes.import_export import bp as import_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(recipes_bp, url_prefix='/recipes')
    app.register_blueprint(categories_bp, url_prefix='/categories')
    app.register_blueprint(import_bp, url_prefix='/import')

    # Create database tables
    with app.app_context():
        db.create_all()
        # Ensure schema is up to date (add any missing columns)
        ensure_schema_updated()
        # Seed default categories if empty
        from app.models.category import Category
        if Category.query.count() == 0:
            seed_categories()

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}

    return app


def ensure_schema_updated():
    """Add any missing columns to existing tables (auto-migration)."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)

    # Check if recipes table exists
    if 'recipes' not in inspector.get_table_names():
        return

    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('recipes')]

    # Add rest_time_minutes if missing
    if 'rest_time_minutes' not in columns:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE recipes ADD COLUMN rest_time_minutes INTEGER'))
            conn.commit()


def seed_categories():
    """Seed default recipe categories."""
    from app.models.category import Category

    default_categories = [
        ('Breakfast', 'Morning meals and brunch dishes', 1),
        ('Lunch', 'Midday meals and light fare', 2),
        ('Dinner', 'Main courses and evening meals', 3),
        ('Appetizers', 'Starters and finger foods', 4),
        ('Soups & Salads', 'Soups, stews, and fresh salads', 5),
        ('Desserts', 'Sweets, cakes, and treats', 6),
        ('Beverages', 'Drinks and cocktails', 7),
        ('Snacks', 'Quick bites and light snacks', 8),
        ('Sides', 'Side dishes and accompaniments', 9),
        ('Sauces & Condiments', 'Dressings, sauces, and dips', 10),
    ]

    for name, description, sort_order in default_categories:
        category = Category(name=name, description=description, sort_order=sort_order)
        db.session.add(category)

    db.session.commit()
