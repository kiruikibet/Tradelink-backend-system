from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User_Profile


class AccountApiTests(APITestCase):
    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "seller",
                "first_name": "Test",
                "last_name": "Seller",
                "email": "seller@example.com",
                "password": "strongpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="seller")
        self.assertTrue(User_Profile.objects.filter(user=user).exists())

    def test_login_returns_tokens_and_user(self):
        User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="strongpass123",
            first_name="Test",
            last_name="Buyer",
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "username_or_email": "buyer",
                "password": "strongpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "buyer")
