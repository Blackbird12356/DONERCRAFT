from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, PromoCode

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("title", "quantity", "unit_price", "total_price", "snapshot_json")

class OrderHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "by_user", "created_at")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "status", "payment_status", "payment_method", "delivery_type", "total")
    list_filter = ("status", "payment_status", "payment_method", "delivery_type")
    search_fields = ("id", "phone", "guest_name", "email")
    inlines = [OrderItemInline, OrderHistoryInline]
    actions = ["mark_confirmed", "mark_cooking", "mark_ready", "mark_out_for_delivery", "mark_completed", "mark_canceled", "mark_paid"]

    def _set_status(self, request, queryset, status):
        for order in queryset:
            old = order.status
            order.status = status
            order.save(update_fields=["status"])
            OrderStatusHistory.objects.create(order=order, from_status=old, to_status=status, by_user=request.user)

    def mark_confirmed(self, request, queryset):
        self._set_status(request, queryset, Order.Status.CONFIRMED)

    def mark_cooking(self, request, queryset):
        self._set_status(request, queryset, Order.Status.COOKING)

    def mark_ready(self, request, queryset):
        self._set_status(request, queryset, Order.Status.READY)

    def mark_out_for_delivery(self, request, queryset):
        self._set_status(request, queryset, Order.Status.OUT_FOR_DELIVERY)

    def mark_completed(self, request, queryset):
        self._set_status(request, queryset, Order.Status.COMPLETED)

    def mark_canceled(self, request, queryset):
        self._set_status(request, queryset, Order.Status.CANCELED)

    def mark_paid(self, request, queryset):
        queryset.update(payment_status=Order.PaymentStatus.PAID)

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "active", "valid_from", "valid_to", "usage_limit", "used_count", "min_order_total")
    list_filter = ("active", "discount_type")
    search_fields = ("code",)
