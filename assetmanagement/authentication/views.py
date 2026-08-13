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

# import the status
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK

from .models import User
from .serializers import UserLoginSerializer, UserRegisterSerializer


class UserRegisterView(CreateAPIView):
    # queryset = User.objects.all()
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


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
