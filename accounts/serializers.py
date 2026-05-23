from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True,min_length=8)

    class Meta:
        model=User
        fields=["id","username", "email","password","date_joined"]

    
    def validate_email(self,value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exist")
        
        return value


    def create(self,validated_data):
        user=User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user

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

        # GENERATE JWT TOKENS
        refresh = RefreshToken.for_user(user)

        return {

            "refresh": str(refresh),

            "access": str(refresh.access_token),

            "user": {

                "id": user.id,

                "username": user.username,

                "email": user.email,
            }
        }