from rest_framework import serializers
from assets.models import Asset
from assets.serializers import CustomImageField


class AdminAssetSerializer(serializers.ModelSerializer):
    original_image = CustomImageField(required=False, allow_null=True)
    predicted_image = CustomImageField(required=False, allow_null=True)

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
        ]
        read_only_fields = ["id", "created_at"]


class AdminAssetStatsSerializer(serializers.Serializer):
    total_assets = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    correct_count = serializers.IntegerField()
    incorrect_count = serializers.IntegerField()
    maintenance_due_count = serializers.IntegerField()
