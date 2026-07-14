from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Asset
from .serializers import AssetSerializer, AssetFeedbackSerializer, AssetDetailsUpdateSerializer


class AssetListCreateView(ListCreateAPIView):
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Asset.objects.all().order_by("-created_at")


class AssetRetrieveView(RetrieveUpdateAPIView):
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Asset.objects.filter(id=self.kwargs["pk"])

    def get_serializer_class(self):
        if self.request.method == "PUT":
            return AssetDetailsUpdateSerializer
        return AssetSerializer


class AssetFeedbackView(UpdateAPIView):
    serializer_class = AssetFeedbackSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Asset.objects.filter(id=self.kwargs["pk"])