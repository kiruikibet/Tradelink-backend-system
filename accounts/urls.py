from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView

from .views import register, profile

urlpatterns = [
    path("register/",register, name="register"),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path("profile/", profile, name="profile"),

]
  
