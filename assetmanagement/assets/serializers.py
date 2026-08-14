import json
from rest_framework import serializers
from django.conf import settings
from .models import Asset, Status
from .services import run_yolo_and_annotate

from drf_spectacular.utils import extend_schema_field


@extend_schema_field({
    "type": "object",
    "properties": {
        "lat": {
            "type": "number",
            "format": "double",
            "description": "Latitude coordinate",
            "example": 27.700769,
        },
        "lng": {
            "type": "number",
            "format": "double",
            "description": "Longitude coordinate",
            "example": 85.300140,
        },
    },
    "required": ["lat", "lng"],
    "example": {"lat": 27.700769, "lng": 85.300140},
})
class CoordinatesJSONField(serializers.JSONField):
    pass


class CustomImageField(serializers.ImageField):
    def to_representation(self, value):
        if not value:
            return None
        url = value.url
        backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:9000')
        if backend_url.endswith('/'):
            backend_url = backend_url[:-1]
        return f"{backend_url}{url}"


class AssetCreateSerializer(serializers.ModelSerializer):
    original_image = CustomImageField(read_only=True)
    predicted_image = CustomImageField(read_only=True)
    image = CustomImageField(source="original_image", required=True, write_only=True)
    coordinates = CoordinatesJSONField(required=True)
    is_newly_created = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "status",
            "original_image",
            "predicted_image",
            "image",
            "label",
            "conf",
            "created_at",
            "coordinates",
            "is_newly_created",
        ]
        read_only_fields = [
            "id",
            "status",
            "original_image",
            "predicted_image",
            "label",
            "conf",
            "created_at",
            "is_newly_created",
        ]

    def validate_coordinates(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Coordinates must be a valid JSON object")
        keys = value.keys()
        if 'lat' not in keys or 'lng' not in keys:
            raise serializers.ValidationError("Both lat and lng must be provided")
        try:
            lat = float(value['lat'])
            lng = float(value['lng'])
            return {"lat": lat, "lng": lng}
        except (ValueError, TypeError):
            raise serializers.ValidationError("Values must be valid numbers")
        

    def get_is_newly_created(self, obj) -> bool:
        return getattr(obj, "is_newly_created", False)


    def create(self, validated_data):
        original_image = validated_data.get('original_image')
        coordinates = validated_data.get('coordinates')
        
        try:
            predicted_image, detected_object = run_yolo_and_annotate(original_image)
        except ValueError as e:
            raise serializers.ValidationError({"error": str(e)})
        except Exception as e:
            raise serializers.ValidationError(
                {"error": "An error occurred during prediction. " + str(e)}
            )

        label_val = detected_object.get("label") if isinstance(detected_object, dict) else None
        conf_val = detected_object.get("confidence") if isinstance(detected_object, dict) else None

        if coordinates and label_val:
            asset, created = Asset.objects.get_or_create(
                coordinates=coordinates,
                label=label_val,
                defaults={
                    "original_image": original_image,
                    "predicted_image": predicted_image,
                    "conf": conf_val,
                    "status": "PENDING",
                }
            )
        else:
            validated_data['predicted_image'] = predicted_image
            validated_data['label'] = label_val
            validated_data['conf'] = conf_val
            validated_data['status'] = "PENDING"
            asset = super().create(validated_data) 
            created = True

        asset.is_newly_created = created
        return asset        


class AssetDetailsAddSerializer(serializers.ModelSerializer):
    is_newly_created = serializers.SerializerMethodField(read_only=True, default=False)
    status = serializers.ChoiceField(choices=Status.choices, default="CORRECT")
    maker = serializers.CharField(required=True, allow_blank=False)
    model_no = serializers.CharField(required=True, allow_blank=False)
    year = serializers.IntegerField(required=True)
    price_jpy = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    size = serializers.CharField(required=True, allow_blank=False)
    maintenance_cycle = serializers.IntegerField(required=True)
    last_maintenance_date = serializers.DateField(required=True)
    next_maintenance_due = serializers.DateField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "status",
            "original_image",
            "predicted_image",
            "label",
            "conf",
            "maker", 
            "model_no", 
            "year",
            "price_jpy",
            "size",
            "maintenance_cycle",
            "last_maintenance_date",
            "next_maintenance_due",
            "notes",
            "created_at",
            "coordinates",
            "is_newly_created",
        ]
        read_only_fields = [
            "id",
            "original_image",
            "predicted_image",
            "label",
            "conf",
            "is_newly_created",
            "created_at",
            "coordinates",
        ]

    def get_is_newly_created(self, obj) -> bool:
        return getattr(obj, "is_newly_created", False)


class AssetRetrieveSerializer(serializers.ModelSerializer):
    original_image = CustomImageField(read_only=True)
    predicted_image = CustomImageField(read_only=True)
    is_newly_created = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "status",
            "original_image",
            "predicted_image",
            "label",
            "conf",
            "maker", 
            "model_no", 
            "year",
            "price_jpy",
            "size",
            "maintenance_cycle",
            "last_maintenance_date",
            "next_maintenance_due",
            "notes",
            "created_at",
            "coordinates",
            "is_newly_created",
        ]
        read_only_fields = fields  # All fields are read-only for retrieval

    def get_is_newly_created(self, obj) -> bool:
        return getattr(obj, "is_newly_created", False)



class AssetFeedbackSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Status.choices)
    original_image = CustomImageField(read_only=True)
    predicted_image = CustomImageField(read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "original_image",
            "predicted_image",
            "label",
            "conf",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "original_image",
            "predicted_image",
            "label",
            "conf",
            "created_at",
        ]

    def validate_status(self, value):
        if value.lower() not in ["correct", "incorrect"]:
            raise serializers.ValidationError("Feedback must be 'correct' or 'incorrect'")
        return value.upper()

