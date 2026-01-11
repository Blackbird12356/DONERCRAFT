from decimal import Decimal
from django.db.models import Prefetch
from catalog.models import Ingredient, IngredientCategory, Allergen
from .models import RuleSet, SizeOption, BaseOption

def get_active_ruleset() -> RuleSet:
    rs = RuleSet.objects.order_by("-updated_at").first()
    if not rs:
        rs = RuleSet.objects.create(name="Default", free_sauces=2, max_sauces_total=4, max_meat_items=2)
    return rs

def get_builder_options() -> dict:
    rs = get_active_ruleset()

    sizes = list(SizeOption.objects.values("id", "code", "name", "base_price"))
    bases = list(BaseOption.objects.filter(is_available=True).values("id", "name", "price"))

    ingredients = Ingredient.objects.select_related("category").prefetch_related("allergens").filter(is_available=True)
    groups = {}
    for ing in ingredients:
        groups.setdefault(ing.type, []).append({
            "id": ing.id,
            "name": ing.name,
            "category": ing.category.name,
            "price": str(ing.price),
            "grams": ing.grams,
            "calories": ing.calories,
            "is_spicy": ing.is_spicy,
            "allergens": [a.code for a in ing.allergens.all()],
        })

    return {
        "ok": True,
        "rules": {
            "free_sauces": rs.free_sauces,
            "max_sauces_total": rs.max_sauces_total,
            "max_meat_items": rs.max_meat_items,
        },
        "sizes": sizes,
        "bases": bases,
        "ingredients_by_type": groups,
    }

def _to_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default

def calculate_build(payload: dict) -> dict:
    """Считает цену и проверяет ограничения. Сервер — источник истины."""
    rs = get_active_ruleset()

    size_id = payload.get("size_id")
    base_id = payload.get("base_id")
    ingredient_ids = payload.get("ingredient_ids") or []
    quantities = payload.get("quantities") or {}  # {"30": 2}

    size = SizeOption.objects.filter(id=size_id).first()
    base = BaseOption.objects.filter(id=base_id, is_available=True).first()

    if not size:
        return {"ok": False, "error": "size_id is required/invalid"}
    if not base:
        return {"ok": False, "error": "base_id is required/invalid"}

    # Load ingredients
    ings = list(Ingredient.objects.prefetch_related("allergens").select_related("category").filter(id__in=ingredient_ids, is_available=True))
    ing_map = {i.id: i for i in ings}

    # Normalize quantities
    normalized = []
    for ing_id in ingredient_ids:
        ing = ing_map.get(int(ing_id))
        if not ing:
            continue
        qty = _to_int(quantities.get(str(ing.id), 1), 1)
        qty = max(1, min(qty, 5))
        normalized.append((ing, qty))

    # Rules checks
    warnings = []
    errors = []

    sauce_count = sum(qty for ing, qty in normalized if ing.type == Ingredient.Type.SAUCE)
    if sauce_count > rs.max_sauces_total:
        errors.append(f"Соусов выбрано {sauce_count}, максимум {rs.max_sauces_total}.")
    meat_count = sum(qty for ing, qty in normalized if ing.type == Ingredient.Type.MEAT)
    if meat_count > rs.max_meat_items:
        errors.append(f"Мясных позиций {meat_count}, максимум {rs.max_meat_items}.")

    # Pricing
    total = Decimal("0")
    total += Decimal(size.base_price)
    total += Decimal(base.price)

    free_sauces_left = rs.free_sauces
    calories = 0
    allergens = set()

    # Sort to make sauce pricing deterministic (first N sauces free)
    for ing, qty in normalized:
        calories += ing.calories * qty
        for a in ing.allergens.all():
            allergens.add(a.code)

        if ing.type == Ingredient.Type.SAUCE:
            # For sauces: first free_sauces units are free
            free_now = min(free_sauces_left, qty)
            paid_now = qty - free_now
            free_sauces_left -= free_now
            if paid_now > 0:
                total += Decimal(ing.price) * Decimal(paid_now)
        else:
            total += Decimal(ing.price) * Decimal(qty)

    if rs.free_sauces < sauce_count:
        warnings.append(f"Соусов выбрано {sauce_count}, бесплатно {rs.free_sauces}, платных {sauce_count - rs.free_sauces}.")

    snapshot = {
        "size": {"id": size.id, "code": size.code, "name": size.name, "base_price": str(size.base_price)},
        "base": {"id": base.id, "name": base.name, "price": str(base.price)},
        "items": [
            {
                "id": ing.id,
                "name": ing.name,
                "type": ing.type,
                "category": ing.category.name,
                "unit_price": str(ing.price),
                "qty": qty,
            } for ing, qty in normalized
        ]
    }

    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    return {
        "ok": True,
        "subtotal": str(total),
        "warnings": warnings,
        "calories": calories,
        "allergens": sorted(allergens),
        "snapshot": snapshot,
    }
