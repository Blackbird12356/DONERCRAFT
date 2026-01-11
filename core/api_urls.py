from django.urls import path
from core import api_views

urlpatterns = [
    # builder
    path("builder/options/", api_views.builder_options, name="api_builder_options"),
    path("builder/calculate/", api_views.builder_calculate, name="api_builder_calculate"),

    # cart
    path("cart/", api_views.cart_get, name="api_cart_get"),
    path("cart/add/", api_views.cart_add, name="api_cart_add"),
    path("cart/update/", api_views.cart_update, name="api_cart_update"),
    path("cart/remove/", api_views.cart_remove, name="api_cart_remove"),

    # checkout + orders
    path("checkout/", api_views.checkout, name="api_checkout"),
    path("orders/<int:order_id>/", api_views.order_get, name="api_order_get"),

    # payments (demo)
    path("payments/simulate-paid/", api_views.simulate_paid, name="api_simulate_paid"),
]
