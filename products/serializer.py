from rest_framework import serializers
from .models import Product,Category,ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields="__all__"

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model=ProductImage
        fields="__all__"

class ProductSerializer(serializers.ModelSerializer):
    created_at=serializers.DateTimeField(format="%Y-%m-%d",read_only=True)
    category=serializers.ReadOnlyField(source="category.name",read_only=True)
    images=ProductImageSerializer(many=True,read_only=True) 
    user=serializers.ReadOnlyField(source="user.username")   

    class Meta:
        model=Product
        fields="__all__"