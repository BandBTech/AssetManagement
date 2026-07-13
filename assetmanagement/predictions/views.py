from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Prediction
from .serializers import PredictionSerializer, PredictionFeedbackSerializer


class PredictAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PredictionSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PredictionListView(ListAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Prediction.objects.all().order_by("-created_at")


class PredictionRetrieveView(RetrieveAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Prediction.objects.filter(id=self.kwargs["pk"])


class PredictionFeedback(UpdateAPIView):
    serializer_class = PredictionFeedbackSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Prediction.objects.filter(id=self.kwargs["pk"])