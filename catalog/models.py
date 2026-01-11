from django.db import models

class IngredientCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

class Allergen(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    class Type(models.TextChoices):
        MEAT = "MEAT", "Мясо"
        VEG = "VEG", "Овощи"
        SAUCE = "SAUCE", "Соусы"
        EXTRA = "EXTRA", "Дополнительно"

    name = models.CharField(max_length=120)
    category = models.ForeignKey(IngredientCategory, on_delete=models.PROTECT, related_name="ingredients")
    type = models.CharField(max_length=16, choices=Type.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grams = models.PositiveIntegerField(default=0)
    calories = models.PositiveIntegerField(default=0)
    is_spicy = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    allergens = models.ManyToManyField(Allergen, blank=True, related_name="ingredients")

    class Meta:
        ordering = ["category__sort_order", "name"]
        unique_together = [("category", "name")]

    def __str__(self):
        return self.name

class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=140)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__sort_order", "name"]
        unique_together = [("category", "name")]

    def __str__(self):
        return self.name
