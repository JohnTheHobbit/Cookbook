"""Unit conversion service."""

# US to Metric conversion factors
CONVERSIONS = {
    # Volume
    'cup': ('ml', 236.588),
    'cups': ('ml', 236.588),
    'tbsp': ('ml', 14.787),
    'tablespoon': ('ml', 14.787),
    'tablespoons': ('ml', 14.787),
    'tsp': ('ml', 4.929),
    'teaspoon': ('ml', 4.929),
    'teaspoons': ('ml', 4.929),
    'fl oz': ('ml', 29.574),
    'fluid ounce': ('ml', 29.574),
    'fluid ounces': ('ml', 29.574),
    'quart': ('L', 0.946),
    'quarts': ('L', 0.946),
    'gallon': ('L', 3.785),
    'gallons': ('L', 3.785),
    'pint': ('ml', 473.176),
    'pints': ('ml', 473.176),

    # Weight
    'oz': ('g', 28.3495),
    'ounce': ('g', 28.3495),
    'ounces': ('g', 28.3495),
    'lb': ('g', 453.592),
    'lbs': ('g', 453.592),
    'pound': ('g', 453.592),
    'pounds': ('g', 453.592),

    # Length
    'inch': ('cm', 2.54),
    'inches': ('cm', 2.54),
    'in': ('cm', 2.54),
}

# Metric to US conversion (reverse)
METRIC_TO_US = {
    # Volume
    'ml': ('tsp', 0.203),  # ml to tsp
    'L': ('quart', 1.057),

    # Weight
    'g': ('oz', 0.0353),
    'kg': ('lb', 2.205),

    # Length
    'cm': ('inch', 0.394),
}

# Smart rounding thresholds for metric
METRIC_ROUND_VALUES = {
    'ml': [5, 10, 15, 25, 50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 400, 450, 500, 750, 1000],
    'g': [5, 10, 15, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 750, 1000],
    'L': [0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5],
    'cm': [1, 2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30],
}


def convert_to_metric(quantity: float, unit: str) -> tuple[float, str]:
    """
    Convert US measurement to metric.

    Args:
        quantity: Numeric quantity
        unit: US unit name

    Returns:
        Tuple of (converted quantity, metric unit)
    """
    if quantity is None:
        return None, unit

    unit_lower = unit.lower() if unit else ''

    if unit_lower not in CONVERSIONS:
        return quantity, unit  # Unknown unit, return as-is

    metric_unit, factor = CONVERSIONS[unit_lower]
    converted = quantity * factor

    # Apply smart rounding
    converted = smart_round_metric(converted, metric_unit)

    return converted, metric_unit


def convert_to_us(quantity: float, unit: str) -> tuple[float, str]:
    """
    Convert metric measurement to US.

    Args:
        quantity: Numeric quantity
        unit: Metric unit name

    Returns:
        Tuple of (converted quantity, US unit)
    """
    if quantity is None:
        return None, unit

    unit_lower = unit.lower() if unit else ''

    if unit_lower not in METRIC_TO_US:
        return quantity, unit  # Unknown unit, return as-is

    us_unit, factor = METRIC_TO_US[unit_lower]
    converted = quantity * factor

    # Round to reasonable precision
    converted = round(converted, 2)

    return converted, us_unit


def smart_round_metric(value: float, unit: str) -> float:
    """
    Round metric values to user-friendly numbers.

    For example, 236.588ml (1 cup) rounds to 250ml.

    Args:
        value: Numeric value
        unit: Metric unit

    Returns:
        Rounded value
    """
    if unit not in METRIC_ROUND_VALUES:
        return round(value, 1)

    thresholds = METRIC_ROUND_VALUES[unit]

    # Find the closest threshold
    closest = min(thresholds, key=lambda x: abs(x - value))

    # Only use the rounded value if it's within 15% of the original
    if abs(closest - value) / value <= 0.15:
        return closest

    # Otherwise, round to a sensible precision
    if value >= 100:
        return round(value / 5) * 5  # Round to nearest 5
    elif value >= 10:
        return round(value)
    else:
        return round(value, 1)


def format_quantity(value: float, unit: str = None) -> str:
    """
    Format a quantity for display.

    Args:
        value: Numeric value
        unit: Optional unit for context

    Returns:
        Formatted string
    """
    if value is None:
        return ''

    # Handle whole numbers
    if value == int(value):
        return str(int(value))

    # Handle common fractions for US units
    us_volume_units = ['cup', 'cups', 'tbsp', 'tablespoon', 'tsp', 'teaspoon']
    if unit and unit.lower() in us_volume_units:
        fractions = {
            0.125: '1/8',
            0.25: '1/4',
            0.33: '1/3',
            0.34: '1/3',
            0.375: '3/8',
            0.5: '1/2',
            0.625: '5/8',
            0.66: '2/3',
            0.67: '2/3',
            0.75: '3/4',
            0.875: '7/8',
        }

        whole = int(value)
        fraction = round(value - whole, 2)

        if fraction in fractions:
            if whole > 0:
                return f'{whole} {fractions[fraction]}'
            return fractions[fraction]

    # Default to decimal
    if value >= 10:
        return str(int(round(value)))
    return str(round(value, 1))


def get_conversion_data() -> dict:
    """
    Get conversion data for JavaScript.

    Returns:
        Dictionary of conversion factors suitable for JSON serialization
    """
    return {
        'us_to_metric': {k: {'unit': v[0], 'factor': v[1]} for k, v in CONVERSIONS.items()},
        'metric_to_us': {k: {'unit': v[0], 'factor': v[1]} for k, v in METRIC_TO_US.items()},
        'round_values': METRIC_ROUND_VALUES
    }
