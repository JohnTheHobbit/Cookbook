from datetime import datetime
from app import db


class Recipe(db.Model):
    """Recipe model."""
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    prep_time_minutes = db.Column(db.Integer)
    cook_time_minutes = db.Column(db.Integer)
    servings = db.Column(db.Integer)
    servings_unit = db.Column(db.String(50), default='servings')
    instructions = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    source = db.Column(db.String(500))
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    ingredients = db.relationship(
        'Ingredient',
        backref='recipe',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Ingredient.sort_order'
    )

    def __repr__(self):
        return f'<Recipe {self.title}>'

    @property
    def total_time_minutes(self):
        """Return total cooking time."""
        prep = self.prep_time_minutes or 0
        cook = self.cook_time_minutes or 0
        return prep + cook

    @property
    def formatted_total_time(self):
        """Return formatted total time string."""
        total = self.total_time_minutes
        if total == 0:
            return None
        hours, minutes = divmod(total, 60)
        if hours > 0:
            return f'{hours}h {minutes}m' if minutes > 0 else f'{hours}h'
        return f'{minutes}m'

    def to_dict(self, include_ingredients=True):
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'prep_time_minutes': self.prep_time_minutes,
            'cook_time_minutes': self.cook_time_minutes,
            'total_time_minutes': self.total_time_minutes,
            'servings': self.servings,
            'servings_unit': self.servings_unit,
            'instructions': self.instructions,
            'notes': self.notes,
            'source': self.source,
            'is_favorite': self.is_favorite,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_ingredients:
            data['ingredients'] = [i.to_dict() for i in self.ingredients]
        return data


class Ingredient(db.Model):
    """Ingredient model."""
    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    quantity = db.Column(db.Float)
    unit = db.Column(db.String(50))
    unit_type = db.Column(db.String(10), default='us')  # 'us' or 'metric'
    name = db.Column(db.String(200), nullable=False)
    preparation = db.Column(db.String(200))
    is_optional = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Ingredient {self.name}>'

    @property
    def formatted(self):
        """Return formatted ingredient string."""
        parts = []
        if self.quantity:
            # Format quantity nicely (e.g., 0.5 -> 1/2)
            parts.append(format_quantity(self.quantity))
        if self.unit:
            parts.append(self.unit)
        parts.append(self.name)
        if self.preparation:
            parts.append(f', {self.preparation}')
        if self.is_optional:
            parts.append(' (optional)')
        return ' '.join(parts)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'recipe_id': self.recipe_id,
            'quantity': self.quantity,
            'unit': self.unit,
            'unit_type': self.unit_type,
            'name': self.name,
            'preparation': self.preparation,
            'is_optional': self.is_optional,
            'sort_order': self.sort_order,
            'formatted': self.formatted
        }


def format_quantity(value):
    """Format a numeric quantity for display."""
    if value is None:
        return ''

    # Handle common fractions
    fractions = {
        0.25: '1/4',
        0.33: '1/3',
        0.5: '1/2',
        0.66: '2/3',
        0.67: '2/3',
        0.75: '3/4',
    }

    # Check if it's a whole number
    if value == int(value):
        return str(int(value))

    # Check for mixed number (whole + fraction)
    whole = int(value)
    fraction = round(value - whole, 2)

    if fraction in fractions:
        if whole > 0:
            return f'{whole} {fractions[fraction]}'
        return fractions[fraction]

    # Default to decimal
    return str(value)
