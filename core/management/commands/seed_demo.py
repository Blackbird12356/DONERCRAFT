from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import IngredientCategory, Ingredient, Allergen, ProductCategory, Product
from builder.models import RuleSet, SizeOption, BaseOption
from orders.models import PromoCode

class Command(BaseCommand):
    help = "Seed demo data for DonerCraft backend"

    def handle(self, *args, **options):
        # RuleSet, sizes, bases
        RuleSet.objects.get_or_create(name="Default", defaults={"free_sauces": 2, "max_sauces_total": 4, "max_meat_items": 2})
        SizeOption.objects.get_or_create(code="S", defaults={"name": "Small", "base_price": 990})
        SizeOption.objects.get_or_create(code="M", defaults={"name": "Medium", "base_price": 1290})
        SizeOption.objects.get_or_create(code="L", defaults={"name": "Large", "base_price": 1590})

        BaseOption.objects.get_or_create(name="Лаваш", defaults={"price": 0, "is_available": True})
        BaseOption.objects.get_or_create(name="Пита", defaults={"price": 100, "is_available": True})

        # Allergens
        lactose, _ = Allergen.objects.get_or_create(code="LACTOSE", defaults={"name": "Лактоза"})
        gluten, _ = Allergen.objects.get_or_create(code="GLUTEN", defaults={"name": "Глютен"})

        # Ingredient categories
        cat_meat, _ = IngredientCategory.objects.get_or_create(name="Мясо", defaults={"sort_order": 10})
        cat_veg, _ = IngredientCategory.objects.get_or_create(name="Овощи", defaults={"sort_order": 20})
        cat_sauce, _ = IngredientCategory.objects.get_or_create(name="Соусы", defaults={"sort_order": 30})
        cat_extra, _ = IngredientCategory.objects.get_or_create(name="Допы", defaults={"sort_order": 40})

        # Ingredients
        chicken, _ = Ingredient.objects.get_or_create(
            category=cat_meat, name="Курица",
            defaults={"type": Ingredient.Type.MEAT, "price": 300, "grams": 120, "calories": 250}
        )
        beef, _ = Ingredient.objects.get_or_create(
            category=cat_meat, name="Говядина",
            defaults={"type": Ingredient.Type.MEAT, "price": 350, "grams": 120, "calories": 290}
        )
        tomato, _ = Ingredient.objects.get_or_create(
            category=cat_veg, name="Помидор",
            defaults={"type": Ingredient.Type.VEG, "price": 80, "grams": 50, "calories": 10}
        )
        cucumber, _ = Ingredient.objects.get_or_create(
            category=cat_veg, name="Огурец",
            defaults={"type": Ingredient.Type.VEG, "price": 80, "grams": 50, "calories": 10}
        )
        garlic, _ = Ingredient.objects.get_or_create(
            category=cat_sauce, name="Чесночный соус",
            defaults={"type": Ingredient.Type.SAUCE, "price": 70, "grams": 30, "calories": 60}
        )
        spicy, _ = Ingredient.objects.get_or_create(
            category=cat_sauce, name="Острый соус",
            defaults={"type": Ingredient.Type.SAUCE, "price": 70, "grams": 30, "calories": 40, "is_spicy": True}
        )
        cheese, _ = Ingredient.objects.get_or_create(
            category=cat_extra, name="Сыр",
            defaults={"type": Ingredient.Type.EXTRA, "price": 150, "grams": 40, "calories": 120}
        )
        cheese.allergens.add(lactose)

        # Products
        pc, _ = ProductCategory.objects.get_or_create(name="Напитки", defaults={"sort_order": 10})
        Product.objects.get_or_create(category=pc, name="Cola 0.5", defaults={"price": 390, "is_available": True})
        Product.objects.get_or_create(category=pc, name="Вода 0.5", defaults={"price": 250, "is_available": True})

        # Promo
        PromoCode.objects.get_or_create(code="DONER10", defaults={
            "discount_type": PromoCode.DiscountType.PERCENT,
            "value": 10,
            "active": True,
            "min_order_total": 1000
        })

        self.stdout.write(self.style.SUCCESS("Demo data created/updated."))
