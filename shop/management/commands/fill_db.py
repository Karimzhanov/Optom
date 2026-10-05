from decimal import Decimal
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from shop.models import Category, Product


IMAGE_URLS = {
'Сахар': 'https://images.unsplash.com/photo-1588195538326-c5b1e9f80a1b?auto=format&fit=crop&w=900&q=80',
'Мука высший сорт': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=900&q=80',
'Рис': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=900&q=80',
'Макароны': 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=900&q=80',
'Масло растительное': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=900&q=80',
'Coca-Cola': 'https://images.unsplash.com/photo-1554866585-cd94860890b7?auto=format&fit=crop&w=900&q=80',
'Fanta': 'https://images.unsplash.com/photo-1629203851122-3726ecdf080e?auto=format&fit=crop&w=900&q=80',
'Sprite': 'https://images.unsplash.com/photo-1625772299848-391b6a2f7c4c?auto=format&fit=crop&w=900&q=80',
'Pepsi': 'https://images.unsplash.com/photo-1629203849820-fdd70d49c38e?auto=format&fit=crop&w=900&q=80',
'Вода 1.5 л': 'https://images.unsplash.com/photo-1548839140-29a749e1cf4d?auto=format&fit=crop&w=900&q=80',
'Чай чёрный': 'https://images.unsplash.com/photo-1597318181409-cf64d0c6c6a6?auto=format&fit=crop&w=900&q=80',
'Чай зелёный': 'https://images.unsplash.com/photo-1556881286-fc6915169721?auto=format&fit=crop&w=900&q=80',
'Кофе растворимый': 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&q=80',
'Шоколад': 'https://images.unsplash.com/photo-1549007994-cb92caebebd?auto=format&fit=crop&w=900&q=80',
'Печенье': 'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=900&q=80',
'Стиральный порошок': 'https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=900&q=80',
'Средство для посуды': 'https://images.unsplash.com/photo-1585832770485-e68a5dbfad52?auto=format&fit=crop&w=900&q=80',
'Мыло': 'https://images.unsplash.com/photo-1607006344380-b6775a0824b7?auto=format&fit=crop&w=900&q=80',
'Горошек консервированный': 'https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?auto=format&fit=crop&w=900&q=80',
'Кукуруза консервированная': 'https://images.unsplash.com/photo-1601598851547-4302969d0f9b?auto=format&fit=crop&w=900&q=80',
'Томатная паста': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=900&q=80',
'Гречка': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=900&q=80',
'Соль': 'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=900&q=80',
'Вафли': 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=900&q=80',
'Конфеты': 'https://images.unsplash.com/photo-1575377427642-087cf684f04d?auto=format&fit=crop&w=900&q=80',

}

DATA = [
    ("🛍️ Бакалея", 1, [
        ("Сахар", "кг", "мешок", 50, "65.00", "60.00", 10, 20),
        ("Мука высший сорт", "кг", "мешок", 50, "42.00", "39.00", 10, 25),
        ("Рис", "кг", "мешок", 25, "95.00", "88.00", 10, 30),
        ("Гречка", "кг", "мешок", 25, "110.00", "102.00", 10, 18),
        ("Макароны", "кг", "мешок", 10, "85.00", "78.00", 10, 15),
        ("Соль", "кг", "мешок", 25, "25.00", "22.00", 10, 20),
        ("Масло растительное", "л", "ящик", 12, "145.00", "138.00", 6, 12),
    ]),
    ("🥤 Напитки", 2, [
        ("Coca-Cola", "шт.", "блок", 6, "75.00", "68.00", 6, 20),
        ("Fanta", "шт.", "блок", 6, "75.00", "68.00", 6, 18),
        ("Sprite", "шт.", "блок", 6, "75.00", "68.00", 6, 16),
        ("Pepsi", "шт.", "блок", 6, "75.00", "68.00", 6, 20),
        ("Вода 1.5 л", "шт.", "блок", 6, "45.00", "40.00", 6, 25),
    ]),
    ("🍵 Чай и кофе", 3, [
        ("Чай чёрный", "шт.", "коробка", 100, "120.00", "105.00", 10, 15),
        ("Чай зелёный", "шт.", "коробка", 100, "135.00", "120.00", 10, 12),
        ("Кофе растворимый", "шт.", "коробка", 24, "180.00", "165.00", 6, 10),
    ]),
    ("🍫 Сладости", 4, [
        ("Шоколад", "шт.", "коробка", 24, "85.00", "75.00", 10, 20),
        ("Печенье", "кг", "коробка", 10, "160.00", "145.00", 10, 14),
        ("Вафли", "кг", "коробка", 8, "175.00", "160.00", 10, 12),
        ("Конфеты", "кг", "коробка", 10, "210.00", "195.00", 10, 15),
    ]),
    ("🧴 Бытовая химия", 5, [
        ("Стиральный порошок", "шт.", "коробка", 12, "180.00", "165.00", 6, 10),
        ("Средство для посуды", "л", "ящик", 12, "130.00", "115.00", 6, 8),
        ("Мыло", "шт.", "коробка", 72, "35.00", "30.00", 12, 10),
    ]),
    ("🥫 Консервы", 6, [
        ("Горошек консервированный", "шт.", "коробка", 24, "95.00", "85.00", 10, 12),
        ("Кукуруза консервированная", "шт.", "коробка", 24, "100.00", "90.00", 10, 12),
        ("Томатная паста", "шт.", "коробка", 24, "75.00", "68.00", 10, 10),
    ]),
]


class Command(BaseCommand):
    help = "Заполняет каталог тестовыми товарами для оптово-розничного магазина."

    def handle(self, *args, **options):
        # A fresh clone has no SQLite tables yet. Make this command safe to run
        # directly after checkout/venv creation, before any ORM query is made.
        self.stdout.write("Проверяю миграции базы данных...")
        call_command("migrate", interactive=False, verbosity=0)

        created_categories = 0
        created_products = 0
        updated_products = 0

        for category_name, sort_order, products in DATA:
            base_slug = slugify(category_name) or f"category-{sort_order}"
            slug = base_slug
            counter = 2
            while Category.objects.filter(slug=slug).exclude(name=category_name).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={"slug": slug, "sort_order": sort_order},
            )
            if created:
                created_categories += 1
            else:
                changed = False
                if not category.slug:
                    category.slug = slug
                    changed = True
                if category.sort_order != sort_order:
                    category.sort_order = sort_order
                    changed = True
                if changed:
                    category.save(update_fields=["slug", "sort_order"])

            for name, unit, package_type, package_quantity, retail, wholesale, min_wholesale, packages in products:
                product, created = Product.objects.get_or_create(
                    category=category,
                    name=name,
                    defaults={
                        "retail_price": Decimal(retail),
                        "wholesale_price": Decimal(wholesale),
                        "unit": unit,
                        "package_type": package_type,
                        "package_quantity": package_quantity,
                        "stock_packages": Decimal(packages),
                        "stock_quantity": Decimal(packages) * Decimal(package_quantity),
                        "min_wholesale_quantity": min_wholesale,
                        "is_active": True,
                        "external_image_url": IMAGE_URLS.get(name, ""),
                    },
                )

                if created:
                    created_products += 1
                else:
                    # Never overwrite admin changes; fill only a missing photo.
                    if not product.image and IMAGE_URLS.get(name) and product.external_image_url != IMAGE_URLS[name]:
                        product.external_image_url = IMAGE_URLS[name]
                        product.save(update_fields=["external_image_url", "updated_at"])
                        updated_products += 1

        self.stdout.write(self.style.SUCCESS(
            f"Готово: категорий добавлено {created_categories}, товаров добавлено {created_products}."
        ))
        self.stdout.write(
            "Существующие товары не перезаписываются. Остатки и цены, изменённые в админке, сохраняются."
        )
