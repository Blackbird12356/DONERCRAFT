from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("title", "item_type", "unit_price", "total_price", "snapshot_json", "created_at")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "session_key", "user", "updated_at")
    search_fields = ("session_key", "user__username", "user__email")
    inlines = [CartItemInline]
