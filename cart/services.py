# cart/services.py
from __future__ import annotations

from decimal import Decimal
from django.db import transaction

from cart.models import Cart, CartItem
from catalog.models import Product
from builder.services import calculate_build



def get_or_create_cart(request) -> Cart:
    # гарантируем наличие session_key
    if not request.session.session_key:
        request.session.save()

    session_key = request.session.session_key
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None

    cart, _ = Cart.objects.get_or_create(
        session_key=session_key,
        defaults={"user": user},
    )

    # если юзер залогинился позже — привяжем
    if user and cart.user_id is None:
        cart.user = user
        cart.save(update_fields=["user"])

    return cart


def cart_to_dict(cart: Cart) -> dict:
    items_qs = cart.items.order_by("id")
    items = []
    subtotal = Decimal("0")

    for it in items_qs:
        subtotal += Decimal(str(it.total_price))
        items.append(
            {
                "id": it.id,
                "item_type": it.item_type,
                "title": it.title,
                "quantity": it.quantity,
                "unit_price": str(it.unit_price),
                "total_price": str(it.total_price),
                "snapshot": it.snapshot_json or {},
            }
        )

    return {
        "ok": True,
        "cart_id": cart.id,
        "subtotal": str(subtotal),
        "items": items,
    }


@transaction.atomic
def add_product_item(cart: Cart, product_id: int, quantity: int = 1) -> dict:
    product = Product.objects.filter(id=product_id, is_available=True).first()
    if not product:
        return {"ok": False, "error": "Product not found/available"}

    qty = max(1, min(int(quantity), 20))
    unit_price = Decimal(str(product.price))

    CartItem.objects.create(
        cart=cart,
        item_type=CartItem.ItemType.PRODUCT,
        quantity=qty,
        title=product.name,
        snapshot_json={
            "product_id": product.id,
            "category": product.category.name if product.category else None,
        },
        unit_price=unit_price,
        total_price=unit_price * qty,
    )
    return cart_to_dict(cart)



@transaction.atomic
def add_builder_item(cart: CartItem, payload: dict, quantity: int = 1) -> dict:
    calc = calculate_build(payload)
    if not calc.get("ok"):
        return {"ok": False, "error": "Invalid build", "details": calc}

    unit_price = Decimal(calc["subtotal"])

    snap = (calc.get("snapshot") or {})
    # 1) пробуем взять имя из snapshot
    pname = (snap.get("product") or {}).get("name")

    # 2) если snapshot не дал имя — берём из Product по product_id (железобетонно)
    if not pname:
        pid = payload.get("product_id")
        if pid:
            pname = Product.objects.filter(id=pid).values_list("name", flat=True).first()

    # 3) финальный fallback
    if not pname:
        pname = "Донер"

    title = f"{pname} ({snap['size']['code']}, {snap['base']['name']})"

    qty = max(1, min(int(quantity), 20))

    CartItem.objects.create(
        cart=cart,
        item_type=CartItem.ItemType.BUILDER,
        quantity=qty,
        title=title,
        snapshot_json=snap,
        unit_price=unit_price,
        total_price=unit_price * qty,
    )

    return cart_to_dict(cart)



@transaction.atomic
def update_item_qty(cart: Cart, item_id: int, quantity: int) -> dict:
    it = cart.items.filter(id=item_id).first()
    if not it:
        return {"ok": False, "error": "Item not found"}

    qty = max(1, min(int(quantity), 20))
    it.quantity = qty
    it.recalc()
    it.save(update_fields=["quantity", "total_price"])
    return cart_to_dict(cart)


@transaction.atomic
def remove_item(cart: Cart, item_id: int) -> dict:
    it = cart.items.filter(id=item_id).first()
    if not it:
        return {"ok": False, "error": "Item not found"}

    it.delete()
    return cart_to_dict(cart)

def clear_cart(cart):
    cart.items.all().delete()
