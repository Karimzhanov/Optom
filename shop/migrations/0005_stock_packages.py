from decimal import Decimal
from django.db import migrations, models


def forwards(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    for product in Product.objects.all():
        package_size = max(int(product.package_quantity or 1), 1)
        # Before this migration stock_quantity was commonly entered as the
        # number of packages in the admin. Preserve that intention.
        product.stock_packages = Decimal(product.stock_quantity)
        product.stock_quantity = Decimal(product.stock_packages) * Decimal(package_size)
        product.save(update_fields=["stock_packages", "stock_quantity"])


def backwards(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    for product in Product.objects.all():
        product.stock_quantity = int(Decimal(product.stock_packages))
        product.save(update_fields=["stock_quantity"])


class Migration(migrations.Migration):
    dependencies = [("shop", "0004_product_packaging_and_order_sale")]
    operations = [
        migrations.AddField(
            model_name="product",
            name="stock_packages",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=14, verbose_name="Остаток упаковок"),
        ),
        migrations.RunPython(forwards, backwards),
    ]
