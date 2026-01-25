from app import db


class UnitConversion(db.Model):
    """Unit conversion reference table."""
    __tablename__ = 'unit_conversions'

    id = db.Column(db.Integer, primary_key=True)
    us_unit = db.Column(db.String(50), nullable=False)
    metric_unit = db.Column(db.String(50), nullable=False)
    conversion_factor = db.Column(db.Float, nullable=False)
    unit_category = db.Column(db.String(50), nullable=False)  # 'volume', 'weight', 'length'

    def __repr__(self):
        return f'<UnitConversion {self.us_unit} -> {self.metric_unit}>'

    @classmethod
    def seed_defaults(cls):
        """Seed default conversion values."""
        from app import db

        conversions = [
            # Volume
            ('cup', 'ml', 236.588, 'volume'),
            ('tbsp', 'ml', 14.787, 'volume'),
            ('tsp', 'ml', 4.929, 'volume'),
            ('fl oz', 'ml', 29.574, 'volume'),
            ('quart', 'L', 0.946, 'volume'),
            ('gallon', 'L', 3.785, 'volume'),
            ('pint', 'ml', 473.176, 'volume'),
            # Weight
            ('oz', 'g', 28.3495, 'weight'),
            ('lb', 'g', 453.592, 'weight'),
            # Length
            ('inch', 'cm', 2.54, 'length'),
        ]

        for us_unit, metric_unit, factor, category in conversions:
            existing = cls.query.filter_by(us_unit=us_unit).first()
            if not existing:
                conversion = cls(
                    us_unit=us_unit,
                    metric_unit=metric_unit,
                    conversion_factor=factor,
                    unit_category=category
                )
                db.session.add(conversion)

        db.session.commit()
