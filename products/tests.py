from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Product


class ProductApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password="strongpass123",
        )
        self.category = Category.objects.create(name="Electronics")

    def authenticate(self):
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_unauthenticated_user_cannot_create_product(self):
        response = self.client.post(
            "/api/products/products/",
            {
                "name": "Phone",
                "description": "Good condition",
                "price": "10000.00",
                "category": self.category.category_id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Product.objects.count(), 0)

    def test_authenticated_user_can_create_product(self):
        self.authenticate()

        response = self.client.post(
            "/api/products/products/",
            {
                "name": "Phone",
                "description": "Good condition",
                "price": "10000.00",
                "category": self.category.category_id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get()
        self.assertEqual(product.user, self.user)
        self.assertEqual(product.name, "Phone")
