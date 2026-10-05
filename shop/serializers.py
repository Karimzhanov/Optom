from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    in_stock = serializers.BooleanField(read_only=True)
    package_label = serializers.CharField(read_only=True)
    stock_label = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "category", "image_url", "retail_price", "wholesale_price",
            "unit", "stock_quantity", "stock_packages", "stock_label", "min_wholesale_quantity",
            "package_type", "package_quantity", "package_label", "in_stock", "is_active",
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return obj.external_image_url


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    price_type = serializers.ChoiceField(choices=[("retail", "Розница"), ("wholesale", "Опт")])


class OrderCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=50)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)
    items = OrderItemInputSerializer(many=True)
