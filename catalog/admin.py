from django.contrib import admin
from .models import IngredientCategory, Allergen, Ingredient, ProductCategory, Product

@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    list_editable = ("sort_order",)
    search_fields = ("name",)

@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "category", "price", "grams", "is_available")
    list_filter = ("type", "category", "is_available", "allergens")
    search_fields = ("name",)
    filter_horizontal = ("allergens",)

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    list_editable = ("sort_order",)
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "is_available")
    list_display_links = ("id", "name")

