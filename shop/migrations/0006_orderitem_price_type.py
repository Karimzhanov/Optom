from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0005_stock_packages"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="price_type",
            field=models.CharField(
                choices=[
                    ("retail", "Розница"),
                    ("wholesale", "Опт"),
                ],
                default="retail",
                max_length=20,
                verbose_name="Тип цены",
            ),
        ),
    ]
