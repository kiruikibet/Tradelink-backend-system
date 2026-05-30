from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Product,Category,ProductImage
from .serializer import ProductSerializer,CategorySerializer,ProductImageSerializer

# Create your views here.
@api_view(["GET","POST"])
def products(request):
    if request.method=="GET":
        products=Product.objects.all()
        serializer=ProductSerializer(products,many=True)
        return Response(serializer.data)
    
    elif request.method=="POST":

        if not request.user.is_authenticated:
            return Response(
                {
                    "message":"Please login to Post Products"
                 },
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer=ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(["GET","POST"])
def categories(request):
    if request.method=="GET":
        categories=Category.objects.all()
        serializer=CategorySerializer(categories,many=True)
        return Response(serializer.data)
    
    elif request.method=="POST":
        if not request.user.is_authenticated:
            return Response(
                {"message":"Only Admins can Post Categories"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer=CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
@api_view(["POST"])
def upload_product_image(request):
    if not request.user.is_authenticated:
        return Response(
            {"message":"Please Login First"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer=ProductImageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

        
    

