from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer, RegisterSerializer
from .models import User_Profile


@api_view(["POST"])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "user registered successfully", "user": serializer.data},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    user_profile, _ = User_Profile.objects.get_or_create(user=request.user)
    return Response({
        "user": {
            "id": request.user.id,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "username": request.user.username,
            "email": request.user.email,
            "bio": user_profile.bio,
            "profile_picture": user_profile.profile_image,
        }
    })


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_avatar(request):
    import cloudinary.uploader

    new_url = request.data.get("profile_picture")
    new_public_id = request.data.get("public_id")  # sent from frontend

    if not new_url:
        return Response(
            {"profile_picture": "Profile picture URL is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user_profile, _ = User_Profile.objects.get_or_create(user=request.user)

    # Delete old image from Cloudinary if it exists
    if user_profile.cloudinary_public_id:
        try:
            cloudinary.uploader.destroy(user_profile.cloudinary_public_id)
        except Exception:
            pass  # don't block the update if delete fails

    user_profile.profile_image = new_url
    if new_public_id:
        user_profile.cloudinary_public_id = new_public_id
    user_profile.save(update_fields=["profile_image", "cloudinary_public_id"])

    return Response({"profile_picture": user_profile.profile_image})


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    data = request.data

    new_username = data.get("username", "").strip()
    if new_username and new_username != user.username:
        if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
            return Response(
                {"username": "Username already taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.username = new_username

    user.first_name = data.get("first_name", user.first_name).strip()
    user.last_name = data.get("last_name", user.last_name).strip()
    user.save(update_fields=["username", "first_name", "last_name"])

    user_profile, _ = User_Profile.objects.get_or_create(user=user)
    user_profile.bio = data.get("bio", user_profile.bio or "")
    user_profile.save(update_fields=["bio"])

    return Response({
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "bio": user_profile.bio,
            "profile_picture": user_profile.profile_image,
        }
    })


@api_view(["GET"])
def check_username(request):
    username = request.query_params.get("username", "").strip()
    if not username:
        return Response({"available": False})
    taken = User.objects.filter(username=username).exists()
    return Response({"available": not taken})
