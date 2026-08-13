from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from assets.models import Asset
from .permissions import IsSuperUser
from .serializers import AdminAssetSerializer, AdminAssetStatsSerializer


class AdminAssetViewSet(viewsets.ModelViewSet):
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
