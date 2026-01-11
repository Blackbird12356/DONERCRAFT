from django.shortcuts import render, get_object_or_404
from orders.models import Order

def landing(request):
    return render(request, "landing.html")

def builder_page(request):
    return render(request, "builder.html")

def cart_page(request):
    return render(request, "cart.html")

def checkout_page(request):
    return render(request, "checkout.html")

def order_success_page(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "order_success.html", {"order": order})
