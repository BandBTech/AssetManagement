from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from .models import Asset
from .serializers import (
    AssetCreateSerializer,
    AssetFeedbackSerializer,
    AssetDetailsAddSerializer,
    AssetRetrieveSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="List all assets",
        description="Returns a list of all recorded assets with their metadata.",
        responses={200: AssetRetrieveSerializer(many=True)},
        tags=["Assets"],
    ),
    post=extend_schema(
        summary="Create / Detect Asset",
        description=(
            "Upload an image (`image`) along with geolocation JSON (`coordinates`: `{\"lat\": 27.7, \"lng\": 85.3}`).\n\n"
            "Runs YOLO model object detection on upload.\n"
            "* **201 Created**: Returns newly created asset (`is_newly_created: true`).\n"
            "* **200 OK**: If an asset with identical coordinates and label already exists, returns the existing asset (`is_newly_created: false`)."
        ),
        request=AssetCreateSerializer,
        responses={
            201: OpenApiResponse(response=AssetCreateSerializer, description="Newly created asset"),
            200: OpenApiResponse(response=AssetRetrieveSerializer, description="Existing asset returned"),
        },
        tags=["Assets"],
    ),
)
class AssetListCreateView(ListCreateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetCreateSerializer
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = serializer.save()

        is_created = getattr(asset, "is_newly_created", True)
        if is_created:
            response_serializer = AssetCreateSerializer(asset, context={"request": request})
            status_code = status.HTTP_201_CREATED
        else:
            response_serializer = AssetRetrieveSerializer(asset, context={"request": request})
            status_code = status.HTTP_200_OK

        return Response(response_serializer.data, status=status_code)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Asset Details",
        description="Get full details of a specific asset by ID.",
        responses={200: AssetRetrieveSerializer},
        tags=["Assets"],
    ),
    put=extend_schema(
        summary="Add / Update Asset Specifications",
        description=(
            "Submit full specification details for an asset (maker, model_no, year, price_jpy, size, "
            "maintenance_cycle, last_maintenance_date, next_maintenance_due, notes)."
        ),
        request=AssetDetailsAddSerializer,
        responses={200: AssetDetailsAddSerializer},
        tags=["Assets"],
    ),
    patch=extend_schema(
        summary="Submit AI Detection Feedback",
        description="Submit feedback for the AI object detection result (`status` must be `'CORRECT'` or `'INCORRECT'`).",
        request=AssetFeedbackSerializer,
        responses={200: AssetFeedbackSerializer},
        tags=["Assets"],
    ),
)
class AssetRetrieveUpdateView(RetrieveUpdateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetCreateSerializer

    def get_serializer_class(self):
        if self.request and self.request.method == "PUT":
            return AssetDetailsAddSerializer
        elif self.request and self.request.method == "PATCH":
            return AssetFeedbackSerializer
        else:
            return AssetRetrieveSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)