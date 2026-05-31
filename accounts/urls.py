from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import register, profile, login, update_avatar

urlpatterns = [
    path("register/",register, name="register"),
    path('login/', login, name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path("profile/", profile, name="profile"),
    path("profile/update-avatar/", update_avatar, name="update_avatar"),

]
  
