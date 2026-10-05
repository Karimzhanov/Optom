import urllib.parse
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Category, Product, Order, OrderItem
from .serializers import CategorySerializer, ProductSerializer, OrderCreateSerializer


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def categories(request):
    return Response(CategorySerializer(Category.objects.all(), many=True).data)


def _normalize_search(value):
    """Normalize Russian/Latin text for forgiving catalogue search."""
    import re
    value = str(value or "").lower().replace("ё", "е")
    # Keep letters/numbers from all alphabets, collapse punctuation/spacing.
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def _product_search_text(product):
    category = product.category
    values = [
        product.name,
        product.description,
        category.name if category else "",
        category.slug if category else "",
        product.unit,
        product.package_type,
        product.package_label,
        product.package_quantity,
        product.retail_price,
        product.wholesale_price,
    ]
    return _normalize_search(" ".join(map(str, values)))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def products(request):
    qs = Product.objects.filter(is_active=True).select_related("category")

    cat = request.GET.get("category", "").strip()
    if cat:
        qs = qs.filter(category__slug=cat)

    q = request.GET.get("q", "").strip()
    if q:
        # Do normalization in Python instead of relying only on SQLite
        # icontains: this makes "ё/е", punctuation and multi-word searches
        # behave consistently in every category.
        words = _normalize_search(q).split()
        if words:
            qs = [product for product in qs if all(
                word in _product_search_text(product) for word in words
            )]

    return Response(
        ProductSerializer(qs, many=True, context={"request": request}).data
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@transaction.atomic
def create_order(request):
    ser = OrderCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    if not data["items"]:
        return Response({"detail": "Корзина пуста."}, status=status.HTTP_400_BAD_REQUEST)

    requested = {}
    for item in data["items"]:
        requested[item["product_id"]] = requested.get(item["product_id"], 0) + item["quantity"]

    products_map = {}
    for product_id, total_qty in requested.items():
        try:
            product = Product.objects.select_for_update().get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"detail": f"Товар #{product_id} не найден."}, status=status.HTTP_400_BAD_REQUEST)

        if product.stock_quantity <= 0:
            return Response({"detail": f"Товар «{product.name}» закончился."}, status=status.HTTP_400_BAD_REQUEST)
        if product.stock_quantity < total_qty:
            return Response(
                {"detail": f"Недостаточно товара «{product.name}». Осталось: {product.stock_label}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        products_map[product.id] = product

    for item in data["items"]:
        product = products_map[item["product_id"]]
        if item["price_type"] == "wholesale" and item["quantity"] < product.min_wholesale_quantity:
            return Response(
                {"detail": f"Для оптовой цены «{product.name}» нужно минимум {product.min_wholesale_quantity} {product.unit}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    order = Order.objects.create(
        customer_name=data["customer_name"],
        phone=data["phone"],
        address=data.get("address", ""),
        comment=data.get("comment", ""),
    )

    total = Decimal("0")
    lines = []
    for item in data["items"]:
        product = products_map[item["product_id"]]
        qty = Decimal(item["quantity"])
        price_type = item["price_type"]
        price = product.wholesale_price if price_type == "wholesale" else product.retail_price
        price_label = "Опт" if price_type == "wholesale" else "Розница"
        line = price * qty
        total += line
        image_url = request.build_absolute_uri(product.image.url) if product.image else product.external_image_url

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=int(qty),
            unit_price=price,
            line_total=line,
            price_type=price_type,
            sale_mode="unit",
            sale_quantity=int(qty),
            sale_unit=product.unit,
            image_url=image_url,
        )

        product.stock_quantity -= qty
        package_size = max(int(product.package_quantity or 1), 1)
        product.stock_packages = product.stock_quantity / Decimal(package_size)
        product.save(update_fields=["stock_quantity", "stock_packages", "updated_at"])
        lines.append((product, int(qty), price, line, image_url, price_label))

    order.total = total
    order.save(update_fields=["total"])

    message = f"Здравствуйте! Хочу оформить заказ в {settings.SHOP_NAME}.\n\n🛒 Мой заказ:\n"
    for i, (product, qty, price, line, image_url, price_label) in enumerate(lines, 1):
        message += f"\n{i}. {product.name}\n   {price_label}: {qty} {product.unit} × {price} сом/{product.unit} — {line} сом"
        if image_url:
            message += f"\n   Фото: {image_url}"
    message += f"\n\n💰 Итого: {total} сом\n👤 Клиент: {order.customer_name}\n📞 Телефон: {order.phone}"
    if order.address:
        message += f"\n📍 Адрес: {order.address}"
    if order.comment:
        message += f"\n💬 Комментарий: {order.comment}"

    wa = f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={urllib.parse.quote(message)}"
    return Response({"order_id": order.id, "total": str(total), "whatsapp_url": wa, "message": message}, status=status.HTTP_201_CREATED)
