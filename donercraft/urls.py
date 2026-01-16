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
        # новые страницы
    path("contacts/", core_views.contacts_page, name="contacts"),
    path("about/", core_views.about_page, name="about"),
    path("menu/", core_views.menu_page, name="menu"),
    path("constructor/", core_views.constructor_page, name="constructor"),

    # api
    path("api/", include("core.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
