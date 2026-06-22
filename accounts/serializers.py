from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User_Profile

class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True,min_length=8)
    account_type=serializers.ChoiceField(choices=["buyer", "seller"], default="buyer", write_only=True)

    class Meta:
        model=User
        fields=["id","last_name","first_name","username", "email","password","account_type","date_joined"]

    
    def validate_email(self,value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exist")        
        return value
    def validate_username(self,value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exist")
        return value

    def validate_password(self,value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def create(self,validated_data):
        account_type = validated_data.pop("account_type", "buyer")
        user=User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        User_Profile.objects.create(user=user, account_type=account_type)
        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=User_Profile
        fields="__all__"
               

class LoginSerializer(serializers.Serializer):

    username_or_email = serializers.CharField()

    password = serializers.CharField(
        write_only=True
    )

    def validate(self, data):

        username_or_email = data.get(
            "username_or_email"
        )

        password = data.get("password")

        # CHECK IF INPUT IS EMAIL
        if "@" in username_or_email:

            try:

                user_obj = User.objects.get(
                    email=username_or_email
                )

                username = user_obj.username

            except User.DoesNotExist:
                raise serializers.ValidationError(
                    "Invalid credentials"
                )

        else:
            username = username_or_email

        # AUTHENTICATE USER
        user = authenticate(
            username=username,
            password=password
        )

        if not user:

            raise serializers.ValidationError(
                "Invalid credentials"
            )

        user_profile, _ = User_Profile.objects.get_or_create(user=user)

        # GENERATE JWT TOKENS
        refresh = RefreshToken.for_user(user)

        return {

            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "first_name":user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email,
                "profile_picture": user_profile.profile_image,
                "account_type": user_profile.account_type,
                "verification_status": user_profile.verification_status,
                "profile": ProfileSerializer(user_profile).data
            }
        }
