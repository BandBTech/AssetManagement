from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Asset
from .serializers import AssetCreateSerializer, AssetFeedbackSerializer, AssetDetailsAddSerializer, AssetRetrieveSerializer


class AssetListCreateView(ListCreateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetCreateSerializer


class AssetRetrieveUpdateView(RetrieveUpdateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetCreateSerializer
    http_method_names = ['get', 'put', 'head', 'options']

    def get_serializer_class(self):
        if self.request and self.request.method == "PUT":
            return AssetDetailsAddSerializer
        return AssetRetrieveSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class AssetFeedbackView(UpdateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetFeedbackSerializer