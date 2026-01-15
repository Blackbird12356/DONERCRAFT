# cart/services.py
from __future__ import annotations

from decimal import Decimal
from django.db import transaction

from cart.models import Cart, CartItem
from catalog.models import Product
from builder.services import calculate_build
from cart.models import CartItem


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
def add_builder_item(cart: Cart, payload: dict, quantity: int = 1) -> dict:
    calc = calculate_build(payload)
    if not calc.get("ok"):
        return calc

    qty = max(1, min(int(quantity), 20))
    total = Decimal(str(calc["total_price"]))
    unit_price = total / qty

    # красивый заголовок в корзине
    size_name = calc["size"]["name"]
    base_name = calc["base"]["name"]
    title = f'{payload.get("title", "Свой донер")} ({size_name}, {base_name})'

    CartItem.objects.create(
        cart=cart,
        item_type=CartItem.ItemType.BUILDER,
        quantity=qty,
        title=title,
        snapshot_json=calc,  # весь расчёт как снапшот
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
    """
    Удаляет все позиции корзины и сбрасывает subtotal.
    """
    CartItem.objects.filter(cart=cart).delete()
