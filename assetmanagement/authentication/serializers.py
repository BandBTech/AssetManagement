from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from .models import User


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "User Registration Example",
            value={
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePassword123",
                "confirm_password": "SecurePassword123",
            },
            request_only=True,
            media_type="application/json",
        ),
    ]
)
class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        help_text="Required username", required=True
    )
    email = serializers.EmailField(
        help_text="User email address", required=True
    )
    password = serializers.CharField(
        write_only=True, min_length=8, required=True
    )
    confirm_password = serializers.CharField(
        write_only=True, required=True
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "confirm_password",
            "email_verified",
        )
        read_only_fields = ("id", "email_verified")

    # validating the user before creating the user.
    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"message": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        return User.objects.create_user(**validated_data)

  
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "User Login Example",
            value={
                "identifier": "john_doe/john@doe.com",
                "password": "SecurePassword123",
            },
            request_only=True,
            media_type="application/json",
        ),
        OpenApiExample(
            "User Login Example (Form Data)",
            value={
                "identifier": "john_doe/john@doe.com",
                "password": "SecurePassword123",
            },
            request_only=True,
            media_type="multipart/form-data",
        ),
    ]
)
class UserLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField( required=True )
    password = serializers.CharField( required=True )

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        user = None
        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                raise AuthenticationFailed(_("Invalid credentials."))

        if user is None or not user.check_password(password):
            raise AuthenticationFailed(_("Invalid credentials."))

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields
