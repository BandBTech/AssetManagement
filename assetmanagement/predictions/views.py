from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Prediction
from .serializers import PredictionSerializer
from .services import run_yolo_and_annotate


class PredictAPIView(APIView):
    permission_classes = [AllowAny]  # change to IsAuthenticated when auth ready

    def post(self, request):
        image = request.FILES.get("image")
        if not image:
            return Response(
                {"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # plot the annotation on the image
            predicted_image, detected_objects = run_yolo_and_annotate(image)

            # save the prediction to the database
            prediction = Prediction.objects.create(
                original_image=image,
                predicted_image=predicted_image,
                detected_objects=detected_objects,
                status="PENDING",
            )

            serializer = PredictionSerializer(prediction, context={"request": request})

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "An error occurred during prediction. " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PredictionListView(ListAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # when auth ready, swap to: return Prediction.objects.filter(user=self.request.user)
        return Prediction.objects.all().order_by("-created_at")


class PredictionRetrieveView(RetrieveAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Prediction.objects.filter(id=self.kwargs["pk"])


class PredictionFeedback(UpdateAPIView):
    pass