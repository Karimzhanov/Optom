from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("shop", "0002_remove_duplicate_products")]
    operations = [
        migrations.AlterField(
            model_name="product",
            name="unit",
            field=models.CharField(
                choices=[("шт.", "Штука (шт.)"), ("кг", "Килограмм (кг)")],
                default="шт.",
                max_length=10,
                verbose_name="Единица измерения",
            ),
        ),
    ]
