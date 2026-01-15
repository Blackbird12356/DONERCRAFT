from django.shortcuts import get_object_or_404, render
from builder.models import SizeOption, BaseOption
from catalog.models import Ingredient
from orders.models import Order

def landing(request):
    sizes = SizeOption.objects.order_by("base_price")
    bases = BaseOption.objects.filter(is_available=True).order_by("price", "name")

    # Только допы (как “Добавить по вкусу”)
    addons = Ingredient.objects.filter(is_available=True, type=Ingredient.Type.EXTRA).order_by("name")

    return render(request, "landing.html", {
        "sizes": sizes,
        "bases": bases,
        "addons": addons,
    })

def builder_page(request):
    return render(request, "builder.html")

def cart_page(request):
    return render(request, "cart.html")

def checkout_page(request):
    return render(request, "checkout.html")

def order_success_page(request, order_id):
    order_obj = get_object_or_404(Order, pk=order_id)

    return render(request, "order_success.html", {
        "order": order_obj
    })
