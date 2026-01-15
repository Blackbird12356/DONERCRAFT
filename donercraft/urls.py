from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # pages
    path("", core_views.landing, name="landing"),
    path("builder/", core_views.builder_page, name="builder_page"),
    path("cart/", core_views.cart_page, name="cart_page"),
    path("checkout/", core_views.checkout_page, name="checkout_page"),
    path("orders/<int:order_id>/success/", core_views.order_success_page, name="order_success_page"),

    # api
    path("api/", include("core.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
