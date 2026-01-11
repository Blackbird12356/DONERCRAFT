from django.db import models

class RuleSet(models.Model):
    """Базовые правила конструктора."""
    name = models.CharField(max_length=80, default="Default")
    free_sauces = models.PositiveIntegerField(default=2)          # сколько соусов бесплатно
    max_sauces_total = models.PositiveIntegerField(default=4)     # максимум соусов можно выбрать
    max_meat_items = models.PositiveIntegerField(default=2)       # максимум мясных ингредиентов (с учетом повторов)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class SizeOption(models.Model):
    code = models.CharField(max_length=8, unique=True)  # S/M/L
    name = models.CharField(max_length=40)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["base_price"]

    def __str__(self):
        return f"{self.name} ({self.code})"

class BaseOption(models.Model):
    name = models.CharField(max_length=60, unique=True)  # лаваш/пита и т.д.
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["price", "name"]

    def __str__(self):
        return self.name
