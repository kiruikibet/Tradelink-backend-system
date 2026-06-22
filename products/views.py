from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Product,Category,ProductImage
from .serializer import ProductSerializer,CategorySerializer,ProductImageSerializer

# Create your views here.
@api_view(["GET", "POST"])
def products(request):
    if request.method == "GET":
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        if not request.user.is_authenticated:
            return Response(
                {"message": "Please login to Post Products"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            profile = getattr(request.user, "user_profile", None)
            if profile and profile.account_type == "seller" and profile.verification_status != "verified":
                return Response(
                    {"message": "Seller verification is required before posting products."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "DELETE", "PATCH"])
def product_detail(request, product_id):
    if not request.user.is_authenticated:
        return Response({"message": "Please login first"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        product = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    # Only the owner can edit or delete
    if product.user != request.user:
        return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "DELETE":
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if request.method == "PATCH":
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

        
    

