from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import RegisterSerializer


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
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


