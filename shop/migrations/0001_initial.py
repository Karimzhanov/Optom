from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[
        migrations.CreateModel(name="Category",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("name",models.CharField(max_length=120,unique=True)),
            ("slug",models.SlugField(max_length=120,unique=True)),
            ("sort_order",models.PositiveIntegerField(default=0)),
        ]),
        migrations.CreateModel(name="Product",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("name",models.CharField(max_length=255)),("description",models.TextField(blank=True)),
            ("image",models.ImageField(blank=True,null=True,upload_to="products/")),
            ("external_image_url",models.URLField(blank=True)),
            ("retail_price",models.DecimalField(decimal_places=2,max_digits=12)),
            ("wholesale_price",models.DecimalField(decimal_places=2,max_digits=12)),
            ("unit",models.CharField(default="шт.",max_length=80)),
            ("stock_quantity",models.PositiveIntegerField(default=0)),
            ("min_wholesale_quantity",models.PositiveIntegerField(default=1)),
            ("is_active",models.BooleanField(default=True)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("updated_at",models.DateTimeField(auto_now=True)),
            ("category",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="products",to="shop.category")),
        ]),
        migrations.CreateModel(name="Order",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("customer_name",models.CharField(max_length=150)),("phone",models.CharField(max_length=50)),
            ("address",models.CharField(blank=True,max_length=500)),("comment",models.TextField(blank=True)),
            ("total",models.DecimalField(decimal_places=2,default=0,max_digits=12)),
            ("status",models.CharField(choices=[("new","Новый"),("processing","В обработке"),("completed","Завершён"),("cancelled","Отменён")],default="new",max_length=20)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name="OrderItem",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("product_name",models.CharField(max_length=255)),("quantity",models.PositiveIntegerField()),
            ("unit_price",models.DecimalField(decimal_places=2,max_digits=12)),("line_total",models.DecimalField(decimal_places=2,max_digits=12)),
            ("image_url",models.URLField(blank=True)),
            ("order",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="items",to="shop.order")),
            ("product",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to="shop.product")),
        ]),
    ]
