from django.db import models
from django.conf import settings

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="carts")
    session_key = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id}"

class CartItem(models.Model):
    class ItemType(models.TextChoices):
        BUILDER = "BUILDER", "Конструктор"
        PRODUCT = "PRODUCT", "Товар"

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=16, choices=ItemType.choices)
    quantity = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=200)
    snapshot_json = models.JSONField(default=dict, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def recalc(self):
        self.total_price = self.unit_price * self.quantity
