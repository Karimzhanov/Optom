from decimal import Decimal
from django.db import models


class Category(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    slug = models.SlugField("URL-идентификатор", max_length=120, unique=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ("шт.", "Штука (шт.)"),
        ("кг", "Килограмм (кг)"),
        ("л", "Литр (л)"),
    ]
    PACKAGE_CHOICES = [
        ("", "Без упаковки"),
        ("мешок", "Мешок"),
        ("блок", "Блок"),
        ("коробка", "Коробка"),
        ("ящик", "Ящик"),
    ]

    name = models.CharField("Название", max_length=255)
    category = models.ForeignKey(Category, verbose_name="Категория", on_delete=models.PROTECT, related_name="products")
    description = models.TextField("Описание", blank=True)
    image = models.ImageField("Изображение", upload_to="products/", blank=True, null=True)
    external_image_url = models.URLField("Ссылка на изображение", blank=True)
    retail_price = models.DecimalField("Розничная цена", max_digits=12, decimal_places=2)
    wholesale_price = models.DecimalField("Оптовая цена", max_digits=12, decimal_places=2)
    unit = models.CharField("Основная единица продажи", max_length=10, choices=UNIT_CHOICES, default="шт.")

    # Internal stock in the main sale unit. This is kept for order calculations.
    stock_quantity = models.DecimalField("Остаток в основной единице", max_digits=14, decimal_places=3, default=0)
    # User-facing stock: number of packages when packaging is configured.
    stock_packages = models.DecimalField("Остаток упаковок", max_digits=14, decimal_places=3, default=0)

    min_wholesale_quantity = models.PositiveIntegerField("Минимальное количество для опта", default=1)
    package_type = models.CharField("Вид упаковки", max_length=20, choices=PACKAGE_CHOICES, blank=True, default="")
    package_quantity = models.PositiveIntegerField(
        "Количество основной единицы в упаковке", default=1,
        help_text="Например: мешок сахара 50 кг → 50; блок напитков 6 шт. → 6.",
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата изменения", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["category", "name"], name="unique_product_name_per_category")]
        verbose_name = "товар"
        verbose_name_plural = "товары"

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    @property
    def package_label(self):
        if not self.package_type or self.package_quantity <= 1:
            return ""
        return f"{self.package_type} — {self.package_quantity} {self.unit}"

    @property
    def stock_label(self):
        if self.stock_quantity <= 0:
            return "Нет в наличии"
        if not self.package_type or self.package_quantity <= 1:
            return f"{self._format_decimal(self.stock_quantity)} {self.unit}"

        packages = self.stock_quantity / Decimal(self.package_quantity)
        whole = int(packages)
        remainder = self.stock_quantity - Decimal(whole * self.package_quantity)
        if remainder == 0:
            return f"{whole} {self.package_type}"
        return f"{whole} {self.package_type} + {self._format_decimal(remainder)} {self.unit}"

    @staticmethod
    def _format_decimal(value):
        value = Decimal(value)
        if value == value.to_integral_value():
            return str(int(value))
        return format(value.normalize(), "f").rstrip("0").rstrip(".")

    def sync_stock(self):
        """Keep internal base-unit stock in sync with the admin's package stock."""
        package_size = max(int(self.package_quantity or 1), 1)
        self.stock_quantity = Decimal(self.stock_packages) * Decimal(package_size)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("new", "Новый"),
        ("processing", "В обработке"),
        ("completed", "Завершён"),
        ("cancelled", "Отменён"),
    ]
    customer_name = models.CharField("Имя клиента", max_length=150)
    phone = models.CharField("Телефон", max_length=50)
    address = models.CharField("Адрес", max_length=500, blank=True)
    comment = models.TextField("Комментарий", blank=True)
    total = models.DecimalField("Итого", max_digits=12, decimal_places=2, default=0)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ #{self.pk} — {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.PROTECT)
    product_name = models.CharField("Название", max_length=255)
    quantity = models.PositiveIntegerField("Количество")
    unit_price = models.DecimalField("Цена за единицу", max_digits=12, decimal_places=2)
    line_total = models.DecimalField("Сумма", max_digits=12, decimal_places=2)
    price_type = models.CharField("Тип цены", max_length=20, choices=[("retail", "Розница"), ("wholesale", "Опт")], default="retail")
    # Kept for old database compatibility. The storefront has no package sale mode.
    sale_mode = models.CharField("Способ продажи", max_length=20, choices=[("unit", "Основная единица"), ("package", "Упаковка")], default="unit")
    sale_quantity = models.PositiveIntegerField("Количество при покупке", default=1)
    sale_unit = models.CharField("Единица при покупке", max_length=30, default="шт.")
    image_url = models.URLField("Ссылка на фото", blank=True)

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"
