from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    created_at=serializers.DateTimeField(format="%Y-%m-%d")
    class Meta:
        model=Product
        fields="__all__"