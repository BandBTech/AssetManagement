from rest_framework import serializers
from django.conf import settings
from .models import Asset
from .services import run_yolo_and_annotate


class CustomImageField(serializers.ImageField):
    def to_representation(self, value):
        if not value:
            return None
        url = value.url
        backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
        if backend_url.endswith('/'):
            backend_url = backend_url[:-1]
        return f"{backend_url}{url}"


class AssetSerializer(serializers.ModelSerializer):
    original_image = CustomImageField(required=False)
    predicted_image = CustomImageField(read_only=True)
    is_newly_created = serializers.SerializerMethodField(read_only=True)

    def get_is_newly_created(self, obj):
        return getattr(obj, "is_newly_created", False)

    class Meta:
        model = Asset
        fields = [
            "id",
            "status",
            "original_image",
            "predicted_image",
            
            "label",# "detected_objects",
            "conf",
            "maker", #"brand",
            "model_no", # "asset_model",
            "year",
            "price_jpy", #"purchase_price",
            "size"
            "maintenance_cycle",
            "last_maintenance_date",
            "next_maintenance_due",
            "notes",

            "created_at",
            "coordinates",
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
        return new_asset


class AssetDetailsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "brand",
            "asset_model",
            "purchase_price",
            "depreciation_rate",
            "maintenance_period",
        ]
    
    def update(self, instance, validated_data):
        instance.brand = validated_data.get('brand', instance.brand)
        instance.asset_model = validated_data.get('asset_model', instance.asset_model)
        instance.purchase_price = validated_data.get('purchase_price', instance.purchase_price)
        instance.depreciation_rate = validated_data.get('depreciation_rate', instance.depreciation_rate)
        instance.maintenance_period = validated_data.get('maintenance_period', instance.maintenance_period)
        instance.save()
        return instance


class AssetFeedbackSerializer(serializers.ModelSerializer):
    status = serializers.CharField()
    original_image = CustomImageField(read_only=True)
    predicted_image = CustomImageField(read_only=True)

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

