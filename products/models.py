from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Product(models.Model):
    product_id=models.AutoField(primary_key=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="products")
    name=models.CharField(max_length=30)
    description=models.TextField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table="Product"


    def __str__(self):
        return self.name
