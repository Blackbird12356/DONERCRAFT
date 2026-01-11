from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from cart.models import Cart
from cart.services import clear_cart
from .models import Order, OrderItem, PromoCode, OrderStatusHistory

def _dec(x) -> Decimal:
    return Decimal(str(x))

def _promo_discount(promo: PromoCode, subtotal: Decimal) -> Decimal:
    if not promo or not promo.is_valid_now(subtotal):
        return Decimal("0")
    if promo.discount_type == PromoCode.DiscountType.PERCENT:
        return (subtotal * promo.value / Decimal("100")).quantize(Decimal("0.01"))
    return min(subtotal, promo.value)

def order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "status": order.status,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "delivery_type": order.delivery_type,
        "address": order.address,
        "phone": order.phone,
        "subtotal": str(order.subtotal),
        "discount_total": str(order.discount_total),
        "delivery_fee": str(order.delivery_fee),
        "total": str(order.total),
        "items": [
            {
                "title": i.title,
                "quantity": i.quantity,
                "unit_price": str(i.unit_price),
                "total_price": str(i.total_price),
                "snapshot": i.snapshot_json,
            } for i in order.items.all()
        ],
        "created_at": order.created_at.isoformat(),
    }

@transaction.atomic
def create_order_from_cart(cart: Cart, payload: dict, promo: PromoCode = None) -> dict:
    if cart.items.count() == 0:
        return {"ok": False, "error": "Cart is empty"}

    delivery_type = payload.get("delivery_type")
    phone = (payload.get("phone") or "").strip()
    guest_name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    address = (payload.get("address") or "").strip()
    comment = (payload.get("comment") or "").strip()
    payment_method = payload.get("payment_method") or Order.PaymentMethod.CASH

    if not phone:
        return {"ok": False, "error": "phone is required"}
    if delivery_type not in (Order.DeliveryType.DELIVERY, Order.DeliveryType.PICKUP):
        return {"ok": False, "error": "delivery_type must be DELIVERY or PICKUP"}
    if delivery_type == Order.DeliveryType.DELIVERY and not address:
        return {"ok": False, "error": "address is required for delivery"}

    subtotal = Decimal("0")
    for it in cart.items.all():
        subtotal += it.total_price

    discount = _promo_discount(promo, subtotal) if promo else Decimal("0")
    delivery_fee = Decimal("0")  # можно позже добавить расчет зоны доставки
    total = (subtotal - discount + delivery_fee).quantize(Decimal("0.01"))

    order = Order.objects.create(
        user=cart.user,
        guest_name=guest_name,
        phone=phone,
        email=email,
        delivery_type=delivery_type,
        address=address,
        comment=comment,
        payment_method=payment_method,
        payment_status=(Order.PaymentStatus.PENDING if payment_method in (Order.PaymentMethod.ONLINE, Order.PaymentMethod.KASPI_QR) else Order.PaymentStatus.UNPAID),
        subtotal=subtotal.quantize(Decimal("0.01")),
        discount_total=discount.quantize(Decimal("0.01")),
        delivery_fee=delivery_fee.quantize(Decimal("0.01")),
        total=total,
        promo_code=(promo if promo and promo.is_valid_now(subtotal) else None),
    )

    for it in cart.items.all():
        OrderItem.objects.create(
            order=order,
            title=it.title,
            quantity=it.quantity,
            unit_price=it.unit_price,
            total_price=it.total_price,
            snapshot_json=it.snapshot_json,
        )

    OrderStatusHistory.objects.create(order=order, from_status="", to_status=order.status, by_user=None)

    # increment promo usage
    if order.promo_code_id and promo:
        promo.used_count = promo.used_count + 1
        promo.save(update_fields=["used_count"])

    clear_cart(cart)

    return {"ok": True, "order": order_to_dict(order), "redirect": f"/orders/{order.id}/success/"}
