from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class User_Profile(models.Model):
    user=models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='user_profile',
        primary_key=True
    )
    profile_image=models.URLField(max_length=500, blank=True, null=True)
    cloudinary_public_id=models.CharField(max_length=255, blank=True, null=True)
    phone_number=models.CharField(max_length=15,unique=True,blank=True, null=True)
    country=models.CharField(max_length=100,blank=True)
    city=models.CharField(max_length=100,blank=True,null=True)
    longitude=models.DecimalField(max_digits=9,decimal_places=6,blank=True,null=True)
    latitude=models.DecimalField(max_digits=9,decimal_places=6,blank=True,null=True)
    ip_address=models.GenericIPAddressField(blank=True,null=True)
    bio=models.TextField(blank=True,null=True)



