/**
 * Home Cookbook - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initIngredientCheckboxes();
    initFavoriteButtons();
    initKitchenMode();
    initIngredientForm();
    initSectionForm();
    initUnitConversion();
});

/**
 * Ingredient Checkboxes - Track which ingredients you've added
 */
function initIngredientCheckboxes() {
    const checkboxes = document.querySelectorAll('.ingredient-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const text = this.closest('li').querySelector('.ingredient-text');
            if (text) {
                text.classList.toggle('checked', this.checked);
            }
        });
    });
}

/**
 * Favorite Button Toggle
 */
function initFavoriteButtons() {
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.btn-favorite');
        if (!btn) return;

        const recipeId = btn.dataset.recipeId;
        if (!recipeId) return;

        // Add animation
        btn.classList.add('animate');
        setTimeout(() => btn.classList.remove('animate'), 400);

        // Let htmx handle the request
    });
}

/**
 * Kitchen Mode - Keep screen on and increase text size
 */
let wakeLock = null;

function initKitchenMode() {
    const toggleBtn = document.querySelector('.kitchen-mode-toggle');
    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', async function() {
        const isActive = document.body.classList.toggle('kitchen-mode-active');

        if (isActive) {
            await enableWakeLock();
            this.innerHTML = '<i class="bi bi-phone-fill me-1"></i>Exit Kitchen Mode';
            this.classList.remove('btn-outline-secondary');
            this.classList.add('btn-primary');
        } else {
            releaseWakeLock();
            this.innerHTML = '<i class="bi bi-phone me-1"></i>Kitchen Mode';
            this.classList.remove('btn-primary');
            this.classList.add('btn-outline-secondary');
        }
    });
}

async function enableWakeLock() {
    if ('wakeLock' in navigator) {
        try {
            wakeLock = await navigator.wakeLock.request('screen');
            console.log('Wake Lock active');
        } catch (err) {
            console.log('Wake Lock error:', err);
        }
    }
}

function releaseWakeLock() {
    if (wakeLock) {
        wakeLock.release();
        wakeLock = null;
        console.log('Wake Lock released');
    }
}

// Re-acquire wake lock when page becomes visible again
document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'visible' && document.body.classList.contains('kitchen-mode-active')) {
        await enableWakeLock();
    }
});

/**
 * Ingredient Form - Dynamic adding/removing
 */
function initIngredientForm() {
    const addBtn = document.getElementById('add-ingredient');
    const container = document.getElementById('ingredients-container');

    if (!addBtn || !container) return;

    addBtn.addEventListener('click', function() {
        addIngredientRow(container);
    });

    // Remove ingredient handler
    container.addEventListener('click', function(e) {
        if (e.target.closest('.btn-remove-ingredient')) {
            const row = e.target.closest('.ingredient-row');
            if (row && container.querySelectorAll('.ingredient-row').length > 1) {
                row.remove();
                reindexIngredients(container);
            }
        }
    });
}

function addIngredientRow(container) {
    const index = container.querySelectorAll('.ingredient-row').length;

    const row = document.createElement('div');
    row.className = 'ingredient-row';
    row.innerHTML = `
        <div class="row g-2 align-items-center">
            <div class="col-2">
                <input type="text" class="form-control form-control-sm"
                       name="ingredient_quantity[]" placeholder="Qty">
            </div>
            <div class="col-2">
                <select class="form-select form-select-sm" name="ingredient_unit[]">
                    <option value="">Unit</option>
                    <option value="cup">cup</option>
                    <option value="cups">cups</option>
                    <option value="tbsp">tbsp</option>
                    <option value="tsp">tsp</option>
                    <option value="oz">oz</option>
                    <option value="lb">lb</option>
                    <option value="g">g</option>
                    <option value="ml">ml</option>
                    <option value="piece">piece</option>
                    <option value="clove">clove</option>
                    <option value="can">can</option>
                    <option value="pkg">pkg</option>
                </select>
            </div>
            <div class="col-4">
                <input type="text" class="form-control form-control-sm"
                       name="ingredient_name[]" placeholder="Ingredient name" required>
            </div>
            <div class="col-2">
                <input type="text" class="form-control form-control-sm"
                       name="ingredient_preparation[]" placeholder="Prep">
            </div>
            <div class="col-1 text-center">
                <input type="checkbox" class="form-check-input"
                       name="ingredient_optional[]" value="${index}" title="Optional">
            </div>
            <div class="col-1">
                <button type="button" class="btn btn-sm btn-remove-ingredient" title="Remove">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
        </div>
    `;

    container.appendChild(row);
}

function reindexIngredients(container) {
    const rows = container.querySelectorAll('.ingredient-row');
    rows.forEach((row, index) => {
        const optionalCheckbox = row.querySelector('input[name="ingredient_optional[]"]');
        if (optionalCheckbox) {
            optionalCheckbox.value = index;
        }
    });
}

/**
 * Unit Conversion Toggle
 */
const CONVERSIONS = {
    'cup': { metric: 'ml', factor: 236.588 },
    'cups': { metric: 'ml', factor: 236.588 },
    'tbsp': { metric: 'ml', factor: 14.787 },
    'tsp': { metric: 'ml', factor: 4.929 },
    'oz': { metric: 'g', factor: 28.3495 },
    'lb': { metric: 'g', factor: 453.592 },
    'fl oz': { metric: 'ml', factor: 29.574 },
    'quart': { metric: 'L', factor: 0.946 },
    'pint': { metric: 'ml', factor: 473.176 }
};

function initUnitConversion() {
    const toggleBtns = document.querySelectorAll('.unit-toggle .btn');
    if (!toggleBtns.length) return;

    toggleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const unit = this.dataset.unit;
            toggleBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            convertUnits(unit);
        });
    });
}

function convertUnits(targetUnit) {
    const ingredients = document.querySelectorAll('.ingredient-item');

    ingredients.forEach(item => {
        const qtyEl = item.querySelector('.ingredient-quantity');
        const unitEl = item.querySelector('.ingredient-unit');

        if (!qtyEl || !unitEl) return;

        const originalQty = parseFloat(qtyEl.dataset.originalQty);
        const originalUnit = qtyEl.dataset.originalUnit;

        if (isNaN(originalQty) || !originalUnit) return;

        if (targetUnit === 'metric' && CONVERSIONS[originalUnit.toLowerCase()]) {
            const conv = CONVERSIONS[originalUnit.toLowerCase()];
            const newQty = smartRound(originalQty * conv.factor, conv.metric);
            qtyEl.textContent = formatQuantity(newQty);
            unitEl.textContent = conv.metric;
        } else {
            qtyEl.textContent = formatQuantity(originalQty);
            unitEl.textContent = originalUnit;
        }
    });
}

function smartRound(value, unit) {
    const roundValues = {
        'ml': [5, 10, 15, 25, 50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 400, 450, 500, 750, 1000],
        'g': [5, 10, 15, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 750, 1000],
        'L': [0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5]
    };

    const thresholds = roundValues[unit];
    if (!thresholds) return Math.round(value);

    const closest = thresholds.reduce((prev, curr) =>
        Math.abs(curr - value) < Math.abs(prev - value) ? curr : prev
    );

    if (Math.abs(closest - value) / value <= 0.15) {
        return closest;
    }

    if (value >= 100) return Math.round(value / 5) * 5;
    if (value >= 10) return Math.round(value);
    return Math.round(value * 10) / 10;
}

function formatQuantity(value) {
    if (value === Math.floor(value)) {
        return value.toString();
    }
    return value.toFixed(1).replace(/\.0$/, '');
}

/**
 * Section Form - Dynamic adding/removing of recipe sections
 */
function initSectionForm() {
    const hasSectionsToggle = document.getElementById('has-sections');
    const simpleMode = document.getElementById('simple-mode');
    const sectionsMode = document.getElementById('sections-mode');
    const addSectionBtn = document.getElementById('add-section');
    const sectionsContainer = document.getElementById('sections-container');

    if (!hasSectionsToggle) return;

    // Toggle between simple and sections mode
    hasSectionsToggle.addEventListener('change', function() {
        if (this.checked) {
            if (simpleMode) simpleMode.style.display = 'none';
            if (sectionsMode) sectionsMode.style.display = 'block';
        } else {
            if (simpleMode) simpleMode.style.display = 'block';
            if (sectionsMode) sectionsMode.style.display = 'none';
        }
    });

    // Add section button
    if (addSectionBtn && sectionsContainer) {
        addSectionBtn.addEventListener('click', function() {
            addSection(sectionsContainer);
        });
    }

    // Delegate events for section operations
    if (sectionsContainer) {
        sectionsContainer.addEventListener('click', function(e) {
            // Remove section
            if (e.target.closest('.btn-remove-section')) {
                const card = e.target.closest('.section-card');
                if (card && sectionsContainer.querySelectorAll('.section-card').length > 1) {
                    card.remove();
                    reindexSections(sectionsContainer);
                }
            }

            // Add ingredient to section
            if (e.target.closest('.add-section-ingredient')) {
                const card = e.target.closest('.section-card');
                const container = card.querySelector('.section-ingredients-container');
                const sectionIndex = parseInt(card.dataset.sectionIndex);
                addSectionIngredient(container, sectionIndex);
            }

            // Remove ingredient from section
            if (e.target.closest('.btn-remove-section-ingredient')) {
                const row = e.target.closest('.ingredient-row');
                const container = row.closest('.section-ingredients-container');
                if (container.querySelectorAll('.ingredient-row').length > 1) {
                    row.remove();
                    const card = container.closest('.section-card');
                    const sectionIndex = parseInt(card.dataset.sectionIndex);
                    reindexSectionIngredients(container, sectionIndex);
                }
            }
        });
    }
}

function addSection(container) {
    const index = container.querySelectorAll('.section-card').length;

    const card = document.createElement('div');
    card.className = 'card mb-4 section-card';
    card.dataset.sectionIndex = index;
    card.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <input type="text" class="form-control form-control-lg section-name-input"
                   name="section[${index}][name]"
                   placeholder="Section Name (e.g., Shell, Filling)">
            <button type="button" class="btn btn-sm btn-outline-danger btn-remove-section ms-2" title="Remove Section">
                <i class="bi bi-trash"></i>
            </button>
        </div>
        <div class="card-body">
            <h6 class="d-flex justify-content-between align-items-center">
                Ingredients
                <button type="button" class="btn btn-success btn-sm add-section-ingredient">
                    <i class="bi bi-plus-lg me-1"></i>Add
                </button>
            </h6>
            <div class="mb-2 text-muted small">
                <div class="row">
                    <div class="col-2">Qty</div>
                    <div class="col-2">Unit</div>
                    <div class="col-3">Ingredient</div>
                    <div class="col-2">Prep</div>
                    <div class="col-1">Opt?</div>
                    <div class="col-2"></div>
                </div>
            </div>
            <div class="section-ingredients-container">
                <div class="ingredient-row">
                    <div class="row g-2 align-items-center">
                        <div class="col-2">
                            <input type="text" class="form-control form-control-sm"
                                   name="section[${index}][ingredient][0][quantity]" placeholder="Qty">
                        </div>
                        <div class="col-2">
                            <select class="form-select form-select-sm" name="section[${index}][ingredient][0][unit]">
                                <option value="">Unit</option>
                                <option value="cup">cup</option>
                                <option value="cups">cups</option>
                                <option value="tbsp">tbsp</option>
                                <option value="tsp">tsp</option>
                                <option value="oz">oz</option>
                                <option value="lb">lb</option>
                                <option value="g">g</option>
                                <option value="ml">ml</option>
                                <option value="piece">piece</option>
                                <option value="clove">clove</option>
                                <option value="can">can</option>
                                <option value="pkg">pkg</option>
                            </select>
                        </div>
                        <div class="col-3">
                            <input type="text" class="form-control form-control-sm"
                                   name="section[${index}][ingredient][0][name]" placeholder="Ingredient">
                        </div>
                        <div class="col-2">
                            <input type="text" class="form-control form-control-sm"
                                   name="section[${index}][ingredient][0][preparation]" placeholder="Prep">
                        </div>
                        <div class="col-1 text-center">
                            <input type="checkbox" class="form-check-input"
                                   name="section[${index}][ingredient][0][optional]" value="true" title="Optional">
                        </div>
                        <div class="col-2">
                            <button type="button" class="btn btn-sm btn-remove-section-ingredient" title="Remove">
                                <i class="bi bi-x-lg"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <h6 class="mt-4">Instructions <span class="text-danger">*</span></h6>
            <textarea class="form-control" name="section[${index}][instructions]" rows="6"
                      placeholder="Instructions for this section..."></textarea>
        </div>
    `;

    container.appendChild(card);
}

function addSectionIngredient(container, sectionIndex) {
    const ingredientIndex = container.querySelectorAll('.ingredient-row').length;

    const row = document.createElement('div');
    row.className = 'ingredient-row';
    row.innerHTML = `
        <div class="row g-2 align-items-center">
            <div class="col-2">
                <input type="text" class="form-control form-control-sm"
                       name="section[${sectionIndex}][ingredient][${ingredientIndex}][quantity]" placeholder="Qty">
            </div>
            <div class="col-2">
                <select class="form-select form-select-sm" name="section[${sectionIndex}][ingredient][${ingredientIndex}][unit]">
                    <option value="">Unit</option>
                    <option value="cup">cup</option>
                    <option value="cups">cups</option>
                    <option value="tbsp">tbsp</option>
                    <option value="tsp">tsp</option>
                    <option value="oz">oz</option>
                    <option value="lb">lb</option>
                    <option value="g">g</option>
                    <option value="ml">ml</option>
                    <option value="piece">piece</option>
                    <option value="clove">clove</option>
                    <option value="can">can</option>
                    <option value="pkg">pkg</option>
                </select>
            </div>
            <div class="col-3">
                <input type="text" class="form-control form-control-sm"
                       name="section[${sectionIndex}][ingredient][${ingredientIndex}][name]" placeholder="Ingredient">
            </div>
            <div class="col-2">
                <input type="text" class="form-control form-control-sm"
                       name="section[${sectionIndex}][ingredient][${ingredientIndex}][preparation]" placeholder="Prep">
            </div>
            <div class="col-1 text-center">
                <input type="checkbox" class="form-check-input"
                       name="section[${sectionIndex}][ingredient][${ingredientIndex}][optional]" value="true" title="Optional">
            </div>
            <div class="col-2">
                <button type="button" class="btn btn-sm btn-remove-section-ingredient" title="Remove">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
        </div>
    `;

    container.appendChild(row);
}

function reindexSections(container) {
    const cards = container.querySelectorAll('.section-card');
    cards.forEach((card, sectionIndex) => {
        card.dataset.sectionIndex = sectionIndex;

        // Update section name input
        const nameInput = card.querySelector('.section-name-input');
        if (nameInput) {
            nameInput.name = `section[${sectionIndex}][name]`;
        }

        // Update instructions textarea
        const instructionsTextarea = card.querySelector('textarea[name*="[instructions]"]');
        if (instructionsTextarea) {
            instructionsTextarea.name = `section[${sectionIndex}][instructions]`;
        }

        // Re-index ingredients within this section
        const ingredientsContainer = card.querySelector('.section-ingredients-container');
        if (ingredientsContainer) {
            reindexSectionIngredients(ingredientsContainer, sectionIndex);
        }
    });
}

function reindexSectionIngredients(container, sectionIndex) {
    const rows = container.querySelectorAll('.ingredient-row');
    rows.forEach((row, ingredientIndex) => {
        // Update all input/select names in this row
        const inputs = row.querySelectorAll('input, select');
        inputs.forEach(input => {
            const name = input.name;
            if (name.includes('[quantity]')) {
                input.name = `section[${sectionIndex}][ingredient][${ingredientIndex}][quantity]`;
            } else if (name.includes('[unit]')) {
                input.name = `section[${sectionIndex}][ingredient][${ingredientIndex}][unit]`;
            } else if (name.includes('[name]')) {
                input.name = `section[${sectionIndex}][ingredient][${ingredientIndex}][name]`;
            } else if (name.includes('[preparation]')) {
                input.name = `section[${sectionIndex}][ingredient][${ingredientIndex}][preparation]`;
            } else if (name.includes('[optional]')) {
                input.name = `section[${sectionIndex}][ingredient][${ingredientIndex}][optional]`;
            }
        });
    });
}

/**
 * Search with debounce
 */
let searchTimeout;
const searchInput = document.querySelector('input[name="q"]');
if (searchInput && searchInput.hasAttribute('data-live-search')) {
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            // htmx handles this
        }, 300);
    });
}
