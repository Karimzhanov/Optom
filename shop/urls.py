from django.urls import path
from .views import categories, products, create_order
urlpatterns=[path("categories/",categories),path("products/",products),path("orders/",create_order)]
