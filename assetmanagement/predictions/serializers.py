from rest_framework import serializers
from .models import Prediction


class PredictionSerializer(serializers.ModelSerializer):
    original_image = serializers.ImageField()
    predicted_image = serializers.ImageField(read_only=True)

    class Meta:
        model = Prediction
        fields = [
            "id",
            "original_image",
            "predicted_image",
            "detected_objects",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "predicted_image",
            "detected_objects",
            "status",
            "created_at",
        ]
