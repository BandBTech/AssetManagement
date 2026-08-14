from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from assets.models import Asset
from drf_spectacular.utils import extend_schema, extend_schema_view
from base.permissions import IsSuperUser
from .serializers import AdminAssetSerializer, AdminAssetStatsSerializer, AdminUserSerializer

User = get_user_model()


@extend_schema_view(
    list=extend_schema(summary="Admin: List Users", tags=["Admin Users"]),
    retrieve=extend_schema(summary="Admin: Get User Details", tags=["Admin Users"]),
    create=extend_schema(summary="Admin: Create User", tags=["Admin Users"]),
    update=extend_schema(summary="Admin: Update User (Full)", tags=["Admin Users"]),
    partial_update=extend_schema(summary="Admin: Update User (Partial)", tags=["Admin Users"]),
    destroy=extend_schema(summary="Admin: Delete User", tags=["Admin Users"]),
)
class AdminUserViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = AdminUserSerializer
    permission_classes = [IsSuperUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "is_staff", "is_superuser", "email_verified"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["id", "username", "email", "date_joined", "last_login"]


@extend_schema_view(
    list=extend_schema(summary="Admin: List Assets", tags=["Admin Assets"]),
    retrieve=extend_schema(summary="Admin: Get Asset Details", tags=["Admin Assets"]),
    create=extend_schema(summary="Admin: Create Asset", tags=["Admin Assets"]),
    update=extend_schema(summary="Admin: Update Asset (Full)", tags=["Admin Assets"]),
    partial_update=extend_schema(summary="Admin: Update Asset (Partial)", tags=["Admin Assets"]),
    destroy=extend_schema(summary="Admin: Delete Asset", tags=["Admin Assets"]),
)
class AdminAssetViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "put", "patch", "delete", "head", "options"]
    queryset = Asset.objects.all()
    serializer_class = AdminAssetSerializer
    permission_classes = [IsSuperUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "year"]
    search_fields = ["maker", "model_no", "notes"]
    ordering_fields = [
        "created_at",
        "last_maintenance_date",
        "next_maintenance_due",
        "price_jpy",
    ]

    @extend_schema(
        summary="Admin: Get Asset Statistics",
        description="Retrieves aggregate metrics including total asset count, status breakdown, and upcoming maintenance.",
        responses={200: AdminAssetStatsSerializer},
        tags=["Admin Assets"],
    )
    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        today = timezone.now().date()
        upcoming_threshold = today + timedelta(days=30)

        total_assets = Asset.objects.count()
        pending_count = Asset.objects.filter(status="PENDING").count()
        correct_count = Asset.objects.filter(status="CORRECT").count()
        incorrect_count = Asset.objects.filter(status="INCORRECT").count()
        maintenance_due_count = Asset.objects.filter(
            next_maintenance_due__lte=upcoming_threshold
        ).count()

        stats_data = {
            "total_assets": total_assets,
            "pending_count": pending_count,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "maintenance_due_count": maintenance_due_count,
        }

        serializer = AdminAssetStatsSerializer(stats_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

