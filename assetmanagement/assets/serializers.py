from rest_framework import serializers
from .models import Asset
from .services import run_yolo_and_annotate


class AssetSerializer(serializers.ModelSerializer):
    original_image = serializers.ImageField(required=False)
    predicted_image = serializers.ImageField(read_only=True)
    is_newly_created = serializers.SerializerMethodField(read_only=True)

    def get_is_newly_created(self, obj):
        return getattr(obj, "is_newly_created", False)

    class Meta:
        model = Asset
        fields = [
            "id",
            "original_image",
            "predicted_image",
            "detected_objects",
            "status",
            "created_at",
            "coordinates",
            "brand",
            "asset_model",
            "purchase_price",
            "depreciation_rate",
            "maintenance_period",
            "is_newly_created",
        ]
        read_only_fields = [
            "predicted_image",
            "detected_objects",
            "status",
            "created_at",
            "is_newly_created",
        ]

    def validate(self, attrs):
        image = self.initial_data.get("image")
        if not image:
            raise serializers.ValidationError({"error": "No image provided"})
        
        attrs["original_image"] = image
        return attrs

    def create(self, validated_data):
        image = validated_data.get('original_image')
        coordinates = validated_data.get('coordinates')
        
        try:
            predicted_image, detected_objects = run_yolo_and_annotate(image)
        except ValueError as e:
            raise serializers.ValidationError({"error": str(e)})
        except Exception as e:
            print(str(e))
            raise serializers.ValidationError(
                {"error": "An error occurred during prediction. " + str(e)}
            )

        # Check if this asset already exists in the database
        if coordinates and detected_objects:
            # Look for an asset with the exact same coordinates and detected objects
            existing_asset = Asset.objects.filter(
                coordinates=coordinates,
                detected_objects=detected_objects
            ).first()

            if existing_asset:
                existing_asset.is_newly_created = False
                return existing_asset

        validated_data['predicted_image'] = predicted_image
        validated_data['detected_objects'] = detected_objects
        validated_data['status'] = "PENDING"
        
        new_asset = super().create(validated_data)
        new_asset.is_newly_created = True
        print("new asset",new_asset)
        return new_asset

class AssetFeedbackSerializer(serializers.ModelSerializer):
    status = serializers.CharField()

    class Meta:
        model = Asset
        fields = [
            "id",
            "original_image",
            "predicted_image",
            "detected_objects",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "original_image",
            "predicted_image",
            "detected_objects",
            "created_at",
        ]

    def validate_status(self, value):
        if value.lower() not in ["correct", "incorrect"]:
            raise serializers.ValidationError({"error": "Feedback must be 'correct' or 'incorrect'"})
        return value.upper()

