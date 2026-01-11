from django.contrib import admin
from .models import RuleSet, SizeOption, BaseOption

@admin.register(RuleSet)
class RuleSetAdmin(admin.ModelAdmin):
    list_display = ("name", "free_sauces", "max_sauces_total", "max_meat_items", "updated_at")

@admin.register(SizeOption)
class SizeOptionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "base_price")
    list_editable = ("base_price",)
    search_fields = ("code", "name")

@admin.register(BaseOption)
class BaseOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_available")
    list_editable = ("price", "is_available")
    search_fields = ("name",)
