from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Category(models.Model):
    category_id=models.AutoField(primary_key=True)
    name=models.CharField(max_length=30)

    class Meta:
        db_table="Category"

    def __str__(self):
        return self.name

class Product(models.Model):
    product_id=models.AutoField(primary_key=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    category=models.ForeignKey(Category,on_delete=models.CASCADE, related_name="products")
    name=models.CharField(max_length=30)
    description=models.TextField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table="Product"

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    image_id=models.AutoField(primary_key=True)
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name="images")
    image=models.ImageField(upload_to="products/")

    class Meta:
        db_table="Product_Images"

    def __str__(self):
        return f"Image for {self.product.name}"
    

