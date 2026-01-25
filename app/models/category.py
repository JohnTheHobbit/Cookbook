from datetime import datetime
from app import db


class Category(db.Model):
    """Recipe category model."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    recipes = db.relationship('Recipe', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

    @property
    def recipe_count(self):
        """Return the number of recipes in this category."""
        return self.recipes.count()

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'recipe_count': self.recipe_count
        }
