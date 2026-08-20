from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from base.permissions import IsSuperUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.utils import extend_schema
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK

from .models import User
from .serializers import UserLoginSerializer, UserRegisterSerializer


@extend_schema(
    summary="Register New User (Superuser only)",
    description="Registers a new user into the system. Requires superuser authorization.",
    request=UserRegisterSerializer,
    tags=["Authentication"],
)
class UserRegisterView(CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [IsSuperUser]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "success": True,
                "data": {"user": UserRegisterSerializer(user).data},
                "message": "User created successfully. Please verify your email.",
            },
            status=HTTP_201_CREATED,
        )


@extend_schema(
    summary="User Login",
    description="Authenticate user with username/email & password to obtain JWT access & refresh tokens.",
    request=UserLoginSerializer,
    responses={200: UserLoginSerializer},
    tags=["Authentication"],
)
class UserLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


@extend_schema(
    summary="Refresh Access Token",
    description="Obtain a new JWT access token using a valid refresh token.",
    tags=["Authentication"],
)
class CustomTokenRefreshView(TokenRefreshView):
    pass
