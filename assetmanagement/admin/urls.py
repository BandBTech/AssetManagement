from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminAssetViewSet

router = DefaultRouter()
router.register(r"assets", AdminAssetViewSet, basename="admin-asset")

urlpatterns = [
    path("", include(router.urls)),
]
