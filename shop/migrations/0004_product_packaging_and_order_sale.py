from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("shop", "0003_alter_product_unit")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="package_type",
            field=models.CharField(
                choices=[
                    ("", "Без упаковки"),
                    ("мешок", "Мешок"),
                    ("блок", "Блок"),
                    ("коробка", "Коробка"),
                    ("ящик", "Ящик"),
                ],
                default="",
                max_length=20,
                verbose_name="Вид упаковки",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="package_quantity",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Например: мешок сахара 50 кг → 50; блок напитков 6 шт. → 6.",
                verbose_name="Количество основной единицы в упаковке",
            ),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="sale_mode",
            field=models.CharField(
                choices=[("unit", "Основная единица"), ("package", "Упаковка")],
                default="unit",
                max_length=20,
                verbose_name="Способ продажи",
            ),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="sale_quantity",
            field=models.PositiveIntegerField(default=1, verbose_name="Количество при покупке"),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="sale_unit",
            field=models.CharField(default="шт.", max_length=30, verbose_name="Единица при покупке"),
        ),
        migrations.AlterField(
            model_name="product",
            name="unit",
            field=models.CharField(
                choices=[("шт.", "Штука (шт.)"), ("кг", "Килограмм (кг)"), ("л", "Литр (л)")],
                default="шт.",
                max_length=10,
                verbose_name="Основная единица продажи",
            ),
        ),
    ]
