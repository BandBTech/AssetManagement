from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminAssetViewSet, AdminUserViewSet

router = DefaultRouter()
router.register(r"assets", AdminAssetViewSet, basename="admin-asset")
router.register(r"users", AdminUserViewSet, basename="admin-user")

urlpatterns = [
    path("", include(router.urls)),
]
