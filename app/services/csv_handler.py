"""CSV import/export handling."""
import csv
import re
from io import StringIO


def parse_recipe_csv(content: str) -> tuple[list[dict], list[str]]:
    """
    Parse CSV content and return a list of recipe dictionaries and any errors.

    Args:
        content: CSV file content as string

    Returns:
        Tuple of (recipes list, errors list)
    """
    recipes = []
    errors = []

    reader = csv.DictReader(StringIO(content))

    for row_num, row in enumerate(reader, start=2):
        try:
            # Validate required fields
            title = row.get('title', '').strip()
            if not title:
                errors.append(f'Row {row_num}: Title is required')
                continue

            ingredients_str = row.get('ingredients', '')
            instructions_str = row.get('instructions', '').strip()

            # Check if this is a sectioned recipe (contains [Section Name] markers)
            has_sections = bool(re.search(r'\[.+?\]', ingredients_str)) or bool(re.search(r'\[.+?\]', instructions_str))

            if has_sections:
                # Parse sectioned recipe
                sections = parse_sections(ingredients_str, instructions_str)
                if not sections:
                    errors.append(f'Row {row_num}: Sectioned recipe must have at least one section with instructions')
                    continue

                recipe = {
                    'title': title,
                    'category': row.get('category', '').strip() or None,
                    'description': row.get('description', '').strip() or None,
                    'prep_time_minutes': parse_int(row.get('prep_time_minutes', '')),
                    'cook_time_minutes': parse_int(row.get('cook_time_minutes', '')),
                    'servings': parse_int(row.get('servings', '')),
                    'servings_unit': row.get('servings_unit', 'servings').strip() or 'servings',
                    'has_sections': True,
                    'sections': sections,
                    'notes': row.get('notes', '').strip() or None,
                    'source': row.get('source', '').strip() or None
                }
            else:
                # Parse simple recipe
                if not instructions_str:
                    errors.append(f'Row {row_num}: Instructions are required')
                    continue

                ingredients = parse_ingredients(ingredients_str)

                recipe = {
                    'title': title,
                    'category': row.get('category', '').strip() or None,
                    'description': row.get('description', '').strip() or None,
                    'prep_time_minutes': parse_int(row.get('prep_time_minutes', '')),
                    'cook_time_minutes': parse_int(row.get('cook_time_minutes', '')),
                    'servings': parse_int(row.get('servings', '')),
                    'servings_unit': row.get('servings_unit', 'servings').strip() or 'servings',
                    'has_sections': False,
                    'ingredients': ingredients,
                    'instructions': instructions_str,
                    'notes': row.get('notes', '').strip() or None,
                    'source': row.get('source', '').strip() or None
                }

            recipes.append(recipe)

        except Exception as e:
            errors.append(f'Row {row_num}: {str(e)}')

    return recipes, errors


def parse_sections(ingredients_str: str, instructions_str: str) -> list[dict]:
    """
    Parse sectioned ingredients and instructions.

    Format:
        ingredients: "[Shell]2 cups flour|1/2 cup butter[Filling]2 cups ricotta|1 cup sugar"
        instructions: "[Shell]Step 1\\nStep 2[Filling]Step 1\\nStep 2"

    Returns:
        List of section dictionaries with name, ingredients, and instructions
    """
    sections = {}

    # Parse ingredients by section
    if ingredients_str:
        # Split by section markers
        section_pattern = r'\[([^\]]+)\]'
        parts = re.split(section_pattern, ingredients_str)

        # parts will be: ['', 'Section1', 'ingredients1', 'Section2', 'ingredients2', ...]
        i = 1
        while i < len(parts):
            section_name = parts[i].strip()
            section_ingredients = parts[i + 1] if i + 1 < len(parts) else ''
            if section_name not in sections:
                sections[section_name] = {'name': section_name, 'ingredients': [], 'instructions': ''}
            sections[section_name]['ingredients'] = parse_ingredients(section_ingredients)
            i += 2

    # Parse instructions by section
    if instructions_str:
        section_pattern = r'\[([^\]]+)\]'
        parts = re.split(section_pattern, instructions_str)

        i = 1
        while i < len(parts):
            section_name = parts[i].strip()
            section_instructions = parts[i + 1] if i + 1 < len(parts) else ''
            if section_name not in sections:
                sections[section_name] = {'name': section_name, 'ingredients': [], 'instructions': ''}
            sections[section_name]['instructions'] = section_instructions.strip()
            i += 2

    # Convert to list and filter out sections without instructions
    result = [s for s in sections.values() if s['instructions']]
    return result


def parse_ingredients(ingredient_string: str) -> list[dict]:
    """
    Parse pipe-separated ingredients string.

    Format: "2 cups flour|1 tsp salt|1/2 cup butter, melted"

    Args:
        ingredient_string: Pipe-separated ingredients

    Returns:
        List of ingredient dictionaries
    """
    ingredients = []

    if not ingredient_string:
        return ingredients

    for item in ingredient_string.split('|'):
        item = item.strip()
        if not item:
            continue

        parsed = parse_single_ingredient(item)
        if parsed:
            ingredients.append(parsed)

    return ingredients


def parse_single_ingredient(text: str) -> dict:
    """
    Parse a single ingredient string.

    Examples:
        "2 cups flour" -> {quantity: 2, unit: 'cups', name: 'flour'}
        "1/2 tsp salt" -> {quantity: 0.5, unit: 'tsp', name: 'salt'}
        "butter, melted" -> {name: 'butter', preparation: 'melted'}
        "salt to taste" -> {name: 'salt to taste'}

    Args:
        text: Ingredient text

    Returns:
        Dictionary with ingredient data
    """
    result = {
        'quantity': None,
        'unit': None,
        'name': '',
        'preparation': None,
        'is_optional': False
    }

    text = text.strip()

    # Check for optional
    if '(optional)' in text.lower():
        result['is_optional'] = True
        text = re.sub(r'\s*\(optional\)\s*', '', text, flags=re.IGNORECASE)

    # Check for preparation (after comma)
    if ',' in text:
        parts = text.split(',', 1)
        text = parts[0].strip()
        result['preparation'] = parts[1].strip()

    # Common units
    units = [
        'cups', 'cup', 'tablespoons', 'tablespoon', 'tbsp', 'teaspoons', 'teaspoon', 'tsp',
        'ounces', 'ounce', 'oz', 'pounds', 'pound', 'lb', 'lbs',
        'grams', 'gram', 'g', 'kilograms', 'kilogram', 'kg',
        'milliliters', 'milliliter', 'ml', 'liters', 'liter', 'L',
        'pinch', 'dash', 'cloves', 'clove', 'heads', 'head',
        'slices', 'slice', 'pieces', 'piece', 'cans', 'can',
        'packages', 'package', 'pkg', 'bunches', 'bunch',
        'sprigs', 'sprig', 'stalks', 'stalk', 'large', 'medium', 'small'
    ]

    # Pattern for quantity + unit + name
    # e.g., "2 cups flour" or "1/2 tsp salt" or "1 1/2 cups sugar"
    pattern = r'^([\d\s./]+)?\s*(' + '|'.join(units) + r')?\s+(.+)$'
    match = re.match(pattern, text, re.IGNORECASE)

    if match:
        quantity_str, unit, name = match.groups()
        if quantity_str:
            result['quantity'] = parse_quantity(quantity_str.strip())
        if unit:
            result['unit'] = unit.lower()
        result['name'] = name.strip()
    else:
        # No match, treat entire text as name
        result['name'] = text

    return result


def parse_quantity(value: str) -> float:
    """
    Parse a quantity string to a float.

    Args:
        value: Quantity string (e.g., "2", "1/2", "1 1/2")

    Returns:
        Float value
    """
    if not value:
        return None

    value = value.strip()

    # Handle fractions
    fraction_map = {
        '1/8': 0.125,
        '1/4': 0.25,
        '1/3': 0.33,
        '3/8': 0.375,
        '1/2': 0.5,
        '5/8': 0.625,
        '2/3': 0.67,
        '3/4': 0.75,
        '7/8': 0.875,
    }

    # Check for mixed number (e.g., "1 1/2")
    parts = value.split()
    if len(parts) == 2:
        try:
            whole = float(parts[0])
            fraction = fraction_map.get(parts[1], 0)
            if fraction == 0 and '/' in parts[1]:
                # Try to parse custom fraction
                num, denom = parts[1].split('/')
                fraction = float(num) / float(denom)
            return whole + fraction
        except (ValueError, ZeroDivisionError):
            pass

    # Check for simple fraction
    if value in fraction_map:
        return fraction_map[value]

    # Try to parse fraction like "3/4"
    if '/' in value:
        try:
            num, denom = value.split('/')
            return float(num) / float(denom)
        except (ValueError, ZeroDivisionError):
            pass

    # Try parsing as float
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value: str) -> int:
    """Parse a string to integer, returning None if invalid."""
    if not value:
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


def format_ingredient(ing) -> str:
    """Format a single ingredient for CSV export."""
    parts = []
    if ing.quantity:
        parts.append(str(ing.quantity))
    if ing.unit:
        parts.append(ing.unit)
    parts.append(ing.name)
    if ing.preparation:
        parts.append(f', {ing.preparation}')
    if ing.is_optional:
        parts.append(' (optional)')
    return ' '.join(parts)


def create_csv_export(recipes) -> str:
    """
    Export recipes to CSV format.

    Args:
        recipes: List of Recipe model instances

    Returns:
        CSV content as string
    """
    output = StringIO()
    fieldnames = [
        'title', 'category', 'description', 'prep_time_minutes', 'cook_time_minutes',
        'servings', 'servings_unit', 'ingredients', 'instructions', 'notes', 'source'
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for recipe in recipes:
        if recipe.has_sections:
            # Format sectioned recipe
            ingredients_parts = []
            instructions_parts = []

            for section in recipe.sections:
                # Format section ingredients
                section_ingredients = [format_ingredient(ing) for ing in section.ingredients]
                if section_ingredients:
                    ingredients_parts.append(f'[{section.name}]' + '|'.join(section_ingredients))

                # Format section instructions
                if section.instructions:
                    instructions_parts.append(f'[{section.name}]{section.instructions}')

            ingredients_str = ''.join(ingredients_parts)
            instructions_str = ''.join(instructions_parts)
        else:
            # Format simple recipe
            ingredients_list = [format_ingredient(ing) for ing in recipe.ingredients]
            ingredients_str = '|'.join(ingredients_list)
            instructions_str = recipe.instructions or ''

        writer.writerow({
            'title': recipe.title,
            'category': recipe.category.name if recipe.category else '',
            'description': recipe.description or '',
            'prep_time_minutes': recipe.prep_time_minutes or '',
            'cook_time_minutes': recipe.cook_time_minutes or '',
            'servings': recipe.servings or '',
            'servings_unit': recipe.servings_unit or 'servings',
            'ingredients': ingredients_str,
            'instructions': instructions_str,
            'notes': recipe.notes or '',
            'source': recipe.source or ''
        })

    return output.getvalue()
