from unicodedata import name
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import register, profile, login, update_avatar, update_profile, check_username,forgot_password,reset_password

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("profile/", profile, name="profile"),
    path("profile/update-avatar/", update_avatar, name="update_avatar"),
    path("profile/update/", update_profile, name="update_profile"),
    path("check-username/", check_username, name="check_username"), 
    path("forgot-password/",forgot_password,name="forgot_password"),     
    path("reset-password/", reset_password, name="reset_password")
]
