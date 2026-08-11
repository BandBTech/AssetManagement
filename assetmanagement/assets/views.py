from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Asset
from .serializers import AssetSerializer, AssetFeedbackSerializer, AssetDetailsUpdateSerializer


class AssetListCreateView(ListCreateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer


class AssetRetrieveUpdateView(RetrieveUpdateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    def get_serializer_class(self):
        if self.request and self.request.method in ["PUT", "PATCH"]:
            return AssetDetailsUpdateSerializer
        return AssetSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(AssetSerializer(instance, context=self.get_serializer_context()).data)


class AssetFeedbackView(UpdateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetFeedbackSerializer