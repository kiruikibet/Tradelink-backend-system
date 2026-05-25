from django.contrib import admin
from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "category_id",
        "name",
    )

    search_fields = (
        "name",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_id",
        "name",
        "user",
        "category",
        "price",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "user__username",
    )

    list_filter = (
        "category",
        "created_at",
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = (
        "image_id",
        "product",
    )

    search_fields = (
        "product__name",
    )