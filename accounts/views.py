from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer

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
    return Response({
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
        }
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

 