import json
from decimal import Decimal
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from builder.services import calculate_build
from cart.services import get_or_create_cart, cart_to_dict, add_builder_item, add_product_item, update_item_qty, remove_item
from orders.services import create_order_from_cart, order_to_dict
from orders.models import Order, PromoCode

def _json(request: HttpRequest):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}

@require_http_methods(["GET"])
def builder_options(request):
    # options без выбора пользователя → считаем как пустой payload
    return JsonResponse(calculate_build({}), safe=False)


@require_http_methods(["POST"])
def builder_calculate(request):
    payload = _json(request)
    result = calculate_build(payload)
    return JsonResponse(result, status=200 if result.get("ok") else 400)

@require_http_methods(["GET"])
def cart_get(request):
    cart = get_or_create_cart(request)
    return JsonResponse(cart_to_dict(cart))

@require_http_methods(["POST"])
def cart_add(request):
    payload = _json(request)
    cart = get_or_create_cart(request)

    item_type = payload.get("item_type")
    qty = int(payload.get("quantity", 1))

    if item_type == "BUILDER":
        result = add_builder_item(cart, payload, qty)
        return JsonResponse(result, status=200 if result.get("ok") else 400)

    if item_type == "PRODUCT":
        product_id = payload.get("product_id")
        result = add_product_item(cart, product_id=product_id, quantity=qty)
        return JsonResponse(result, status=200 if result.get("ok") else 400)

    return JsonResponse({"ok": False, "error": "Unknown item_type"}, status=400)

@require_http_methods(["POST"])
def cart_update(request):
    payload = _json(request)
    cart = get_or_create_cart(request)
    item_id = payload.get("item_id")
    qty = int(payload.get("quantity", 1))
    result = update_item_qty(cart, item_id=item_id, quantity=qty)
    return JsonResponse(result, status=200 if result.get("ok") else 400)

@require_http_methods(["POST"])
def cart_remove(request):
    payload = _json(request)
    cart = get_or_create_cart(request)
    item_id = payload.get("item_id")
    result = remove_item(cart, item_id=item_id)
    return JsonResponse(result, status=200 if result.get("ok") else 400)

@require_http_methods(["POST"])
def checkout(request):
    payload = _json(request)
    cart = get_or_create_cart(request)

    promo_code = (payload.get("promo_code") or "").strip().upper()
    promo = None
    if promo_code:
        promo = PromoCode.objects.filter(code=promo_code, active=True).first()

    result = create_order_from_cart(cart, payload, promo=promo)
    return JsonResponse(result, status=200 if result.get("ok") else 400)

@require_http_methods(["GET"])
def order_get(request, order_id: int):
    order = Order.objects.prefetch_related("items").filter(pk=order_id).first()
    if not order:
        return JsonResponse({"ok": False, "error": "Order not found"}, status=404)
    return JsonResponse({"ok": True, "order": order_to_dict(order)})

@require_http_methods(["POST"])
def simulate_paid(request):
    payload = _json(request)
    order_id = payload.get("order_id")
    order = Order.objects.filter(pk=order_id).first()
    if not order:
        return JsonResponse({"ok": False, "error": "Order not found"}, status=404)
    order.payment_status = Order.PaymentStatus.PAID
    order.save(update_fields=["payment_status"])
    return JsonResponse({"ok": True, "order_id": order.id, "payment_status": order.payment_status})
