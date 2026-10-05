from django.db import migrations, models


def remove_duplicates(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    seen = set()
    duplicates = []
    for product in Product.objects.order_by("category_id", "name", "id"):
        key = (product.category_id, product.name.strip().casefold())
        if key in seen:
            duplicates.append(product.pk)
        else:
            seen.add(key)
    if duplicates:
        Product.objects.filter(pk__in=duplicates).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("shop", "0001_initial")]
    operations = [
        migrations.RunPython(remove_duplicates, noop),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(fields=("category", "name"), name="unique_product_name_per_category"),
        ),
    ]
