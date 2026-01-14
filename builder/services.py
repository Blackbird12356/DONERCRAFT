from decimal import Decimal
from catalog.models import Ingredient, Product
from .models import RuleSet, SizeOption, BaseOption

def _to_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

def calculate_build(payload: dict) -> dict:
    """Считает цену и проверяет ограничения. Сервер — источник истины."""
    rs = RuleSet.objects.order_by("-updated_at").first()

    # --- product ---
    product_id = payload.get("product_id")
    product = None
    if product_id:
        product = Product.objects.filter(id=product_id, is_available=True).first()
    if not product:
        return {"ok": False, "error": "product_id is invalid"}

    # --- options ---
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

    # --- load ingredients ---
    ings = list(
        Ingredient.objects
        .prefetch_related("allergens")
        .select_related("category")
        .filter(id__in=ingredient_ids, is_available=True)
    )
    ing_map = {i.id: i for i in ings}

    # --- normalize quantities ---
    normalized = []
    for ing_id in ingredient_ids:
        ing = ing_map.get(int(ing_id))
        if not ing:
            continue
        qty = _to_int(quantities.get(str(ing.id), 1), 1)
        qty = max(1, min(qty, 5))
        normalized.append((ing, qty))

    # --- rules ---
    warnings, errors = [], []

    sauce_count = sum(qty for ing, qty in normalized if ing.type == Ingredient.Type.SAUCE)
    if sauce_count > rs.max_sauces_total:
        errors.append(f"Соусов выбрано {sauce_count}, максимум {rs.max_sauces_total}.")

    meat_count = sum(qty for ing, qty in normalized if ing.type == Ingredient.Type.MEAT)
    if meat_count > rs.max_meat_items:
        errors.append(f"Мясных позиций {meat_count}, максимум {rs.max_meat_items}.")

    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    # --- pricing ---
    total = Decimal("0")

    # size.code ожидается "1.0" / "1.5" / "2.0"
    try:
        mult = Decimal(str(size.code))
    except Exception:
        mult = Decimal("1.0")

    total += Decimal(str(product.price)) * mult
    total += Decimal(str(base.price))

    free_sauces_left = rs.free_sauces
    calories = 0
    allergens = set()

    items_snapshot = []
    for ing, qty in normalized:
        calories += (ing.calories or 0) * qty

        for a in ing.allergens.all():
            allergens.add(a.code)

        unit = Decimal(str(ing.price))
        added = Decimal("0")

        if ing.type == Ingredient.Type.SAUCE:
            free_now = min(free_sauces_left, qty)
            paid_now = qty - free_now
            free_sauces_left -= free_now
            if paid_now > 0:
                added = unit * Decimal(paid_now)
        else:
            added = unit * Decimal(qty)

        total += added

        items_snapshot.append({
            "id": ing.id,
            "name": ing.name,
            "type": ing.type,
            "qty": qty,
            "unit_price": str(unit),
            "added_price": str(added),
        })

    if rs.free_sauces < sauce_count:
        warnings.append(
            f"Соусов выбрано {sauce_count}, бесплатно {rs.free_sauces}, платных {sauce_count - rs.free_sauces}."
        )

    snapshot = {
        "product": {"id": product.id, "name": product.name, "price": str(product.price)},
        "size": {"id": size.id, "code": str(size.code), "name": size.name, "base_price": str(size.base_price)},
        "base": {"id": base.id, "name": base.name, "price": str(base.price)},
        "items": items_snapshot,
    }

    return {
        "ok": True,
        "subtotal": str(total.quantize(Decimal("1"))),
        "warnings": warnings,
        "calories": calories,
        "allergens": sorted(allergens),
        "snapshot": snapshot,
    }
