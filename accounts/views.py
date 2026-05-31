from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer
from .models import User_Profile

from .serializers import RegisterSerializer



@api_view(["POST"])
def login(request):
    serializer=LoginSerializer(data=request.data)

    if serializer.is_valid():
        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )
    
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )

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
            "profile_picture": user_profile.profile_image,
        }
    })

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_avatar(request):
    image_url = request.data.get("profile_picture")

    if not image_url:
        return Response(
            {"profile_picture": "Profile picture URL is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user_profile, _ = User_Profile.objects.get_or_create(user=request.user)
    user_profile.profile_image = image_url
    user_profile.save(update_fields=["profile_image"])

    return Response({
        "profile_picture": user_profile.profile_image,
        "message": "Profile picture updated successfully",
    })
@api_view(["POST"])
def register(request):
    serializer=RegisterSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(
            {
                "message":"user registered successfully",
                "user":serializer.data
            },
            status=status.HTTP_201_CREATED,
        )
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

 
