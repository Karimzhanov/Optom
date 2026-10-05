from django.contrib import admin
from django.utils.text import slugify

from .models import Category, Product, Order, OrderItem

admin.site.site_header = "Optom Product Osh — управление магазином"
admin.site.site_title = "Optom Product Osh"
admin.site.index_title = "Панель управления магазином"
admin.site.empty_value_display = "—"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "products_count")
    list_display_links = ("name",)
    search_fields = ("name",)
    ordering = ("sort_order", "name")
    exclude = ("slug",)

    @admin.display(description="Товаров")
    def products_count(self, obj):
        return obj.products.count()

    def save_model(self, request, obj, form, change):
        base = slugify(obj.name)
        if not base:
            base = "category"
        slug = base
        counter = 2
        while Category.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1
        obj.slug = slug
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "unit", "package_type", "package_quantity",
        "retail_price", "wholesale_price", "min_wholesale_quantity",
        "stock_label_admin", "is_active",
    )
    list_filter = ("category", "unit", "package_type", "is_active")
    search_fields = ("name",)
    list_editable = ("retail_price", "wholesale_price", "is_active")
    list_select_related = ("category",)
    ordering = ("category", "name")
    exclude = ("description",)
    fieldsets = (
        ("Основная информация", {"fields": ("name", "category", "image", "external_image_url", "is_active")}),
        ("Цены", {"fields": ("retail_price", "wholesale_price", "min_wholesale_quantity")}),
        ("Единицы и упаковка", {"fields": ("unit", "package_type", "package_quantity", "stock_packages")} ),
        ("Служебная информация", {"fields": ("created_at", "updated_at", "stock_quantity"), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at", "updated_at", "stock_quantity")

    @admin.display(description="Остаток")
    def stock_label_admin(self, obj):
        return obj.stock_label

    def save_model(self, request, obj, form, change):
        obj.sync_stock()
        super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = (
        "product", "product_name", "quantity", "price_type", "sale_mode",
        "sale_quantity", "sale_unit", "unit_price", "line_total", "image_url",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "phone", "total", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "phone", "address")
    readonly_fields = ("total", "created_at")
    inlines = (OrderItemInline,)
    ordering = ("-created_at",)
