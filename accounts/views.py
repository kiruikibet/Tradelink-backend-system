from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer, RegisterSerializer
from .models import User_Profile
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_bytes,force_str

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
            "account_type": user_profile.account_type,
            "verification_status": user_profile.verification_status,
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
            "account_type": user_profile.account_type,
            "verification_status": user_profile.verification_status,
        }
    })


@api_view(["GET"])
def check_username(request):
    username = request.query_params.get("username", "").strip()
    if not username:
        return Response({"available": False})
    taken = User.objects.filter(username=username).exists()
    return Response({"available": not taken})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_list(request):
    """Admin-only endpoint to list all users."""
    if not request.user.is_staff:
        return Response({"message": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
    users = User.objects.all().values("id", "username", "email", "date_joined", "is_active")
    return Response(list(users))

@api_view(["POST"])
def forgot_password(request):
    email=request.data.get("email")
    if not email:
        return Response(
            {"email":"Email is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user=User.objects.get(email=email)

        #encode user ID into a safe format
        uid=urlsafe_base64_encode(force_bytes(user.pk))
        
        #create secure token
        token= default_token_generator.make_token(user)

        #creating reset link
        reset_link=f"http://localhost:5173/reset-password/{uid}/{token}/"

        #send email
        send_mail(
            subject="Password Reset Request",
            message=f"Click the link to reset your password: \n\n{reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

    except User.DoesNotExist:    
        pass

    return Response({
            "message":"If an account exists with that email, a password reset email has been sent."
        })
    
@api_view(["POST"])
def reset_password(request):
    uid= request.data.get("uid")
    token=request.data.get("token")
    new_password=request.data.get("password")

    if not uid:
        return Response(
            {"uid":"Reset link is missing a user id."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not token:
        return Response(
            {"token":"Reset link is missing a token."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not new_password:
        return Response(
            {"password":"New password is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        #decode user ID
        user_id=force_str(urlsafe_base64_decode(uid))
        user=User.objects.get(pk=user_id)

        #check token validity
        if not default_token_generator.check_token(user, token):
            return Response(
                {"message": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user)
        except ValidationError as exc:
            return Response(
                {"password": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response({
            "message": "Password reset successfully."
        })
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({
            "message":"Invalid or expired reset link."
        },
        status=status.HTTP_400_BAD_REQUEST
        )
