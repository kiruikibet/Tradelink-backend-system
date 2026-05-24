from django.urls import path
from . import views

urlpatterns = [
    path("products/", views.products),
    path("categories/", views.categories),
    path("upload-image/", views.upload_product_image),
]