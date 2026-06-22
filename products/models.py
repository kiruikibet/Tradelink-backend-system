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
    STATUS_AVAILABLE = "available"
    STATUS_NEGOTIATING = "negotiating"
    STATUS_PENDING_CONFIRMATION = "pending_buyer_confirmation"
    STATUS_AWAITING_PAYMENT = "awaiting_payment"
    STATUS_SOLD_PENDING_RELEASE = "sold_pending_release"
    STATUS_BOOKED = "booked"
    STATUS_PENDING_BOOKING = "pending_booking_confirmation"
    STATUS_DISPUTE = "dispute"
    STATUS_COMPLETED = "completed"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "Available"),
        (STATUS_NEGOTIATING, "Negotiating"),
        (STATUS_PENDING_CONFIRMATION, "Pending Buyer Confirmation"),
        (STATUS_AWAITING_PAYMENT, "Awaiting Payment"),
        (STATUS_SOLD_PENDING_RELEASE, "Sold Pending Release"),
        (STATUS_BOOKED, "Booked"),
        (STATUS_PENDING_BOOKING, "Pending Booking Confirmation"),
        (STATUS_DISPUTE, "Dispute"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_EXPIRED, "Expired"),
    ]
    product_id=models.AutoField(primary_key=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    category=models.ForeignKey(Category,on_delete=models.CASCADE, related_name="products")
    name=models.CharField(max_length=30)
    description=models.TextField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    status=models.CharField(max_length=40, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        db_table="Product"

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    image_id=models.AutoField(primary_key=True)
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name="images")
    image=models.URLField(max_length=500)

    class Meta:
        db_table="Product_Images"

    def __str__(self):
        return f"Image for {self.product.name}"
    

