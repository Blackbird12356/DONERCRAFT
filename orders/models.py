from django.db import models
from django.conf import settings
from django.utils import timezone

class PromoCode(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = "PERCENT", "Процент"
        FIXED = "FIXED", "Фикс"

    code = models.CharField(max_length=32, unique=True)
    discount_type = models.CharField(max_length=12, choices=DiscountType.choices)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    min_order_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def is_valid_now(self, subtotal):
        if not self.active:
            return False
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        if subtotal < self.min_order_total:
            return False
        return True

    def __str__(self):
        return self.code

class Order(models.Model):
    class DeliveryType(models.TextChoices):
        DELIVERY = "DELIVERY", "Доставка"
        PICKUP = "PICKUP", "Самовывоз"

    class Status(models.TextChoices):
        NEW = "NEW", "Новый"
        CONFIRMED = "CONFIRMED", "Подтвержден"
        COOKING = "COOKING", "Готовится"
        READY = "READY", "Готов"
        OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", "В доставке"
        COMPLETED = "COMPLETED", "Завершен"
        CANCELED = "CANCELED", "Отменен"

    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Наличные"
        ONLINE = "ONLINE", "Онлайн"
        KASPI_QR = "KASPI_QR", "Kaspi QR (демо)"

    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", "Не оплачено"
        PENDING = "PENDING", "Ожидание"
        PAID = "PAID", "Оплачено"
        FAILED = "FAILED", "Ошибка"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")

    guest_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)

    delivery_type = models.CharField(max_length=12, choices=DeliveryType.choices)
    address = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=24, choices=Status.choices, default=Status.NEW)

    payment_method = models.CharField(max_length=12, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    payment_status = models.CharField(max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    promo_code = models.ForeignKey(PromoCode, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    snapshot_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.title

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=24)
    to_status = models.CharField(max_length=24)
    by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
