from rest_framework import serializers
from .models import Prediction
from .services import run_yolo_and_annotate


class PredictionSerializer(serializers.ModelSerializer):
    original_image = serializers.ImageField(required=False)
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


    def validate(self, attrs):
        image = self.initial_data.get("image")
        if not image:
            raise serializers.ValidationError({"error": "No image provided"})
        
        attrs["original_image"] = image
        return attrs

    def create(self, validated_data):
        image = validated_data.get('original_image')
        
        try:
            predicted_image, detected_objects = run_yolo_and_annotate(image)
        except ValueError as e:
            raise serializers.ValidationError({"error": str(e)})
        except Exception as e:
            print(str(e))
            raise serializers.ValidationError(
                {"error": "An error occurred during prediction. " + str(e)}
            )

        validated_data['predicted_image'] = predicted_image
        validated_data['detected_objects'] = detected_objects
        validated_data['status'] = "PENDING"
        
        return super().create(validated_data)


class PredictionFeedbackSerializer(serializers.ModelSerializer):
    status = serializers.CharField()

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

