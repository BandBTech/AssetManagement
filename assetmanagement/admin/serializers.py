from rest_framework import serializers
from assets.models import Asset
from assets.serializers import CustomImageField
from authentication.models import User

# User = get_user_model()


class AdminAssetSerializer(serializers.ModelSerializer):
    original_image = CustomImageField(required=False, allow_null=True)
    predicted_image = CustomImageField(required=False, allow_null=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "user",
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


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "email_verified",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

