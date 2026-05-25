from django.contrib import admin
from .models import User_Profile


@admin.register(User_Profile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone_number",
        "country",
        "city"
    )

    search_fields = (
        "user__username",
        "phone_number",
        "country",
        "city"
    )

    list_filter = (
        "country",
        "city"
    )