from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from admin.permissions import IsSuperUser
from assets.models import Asset
from admin.serializers import AdminAssetSerializer, AdminAssetStatsSerializer

User = get_user_model()


class IsSuperUserPermissionTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsSuperUser()
        self.superuser = User.objects.create_superuser(
            username="super", email="super@example.com", password="password"
        )
        self.regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="password"
        )

    def test_superuser_has_permission(self):
        request = self.factory.get("/")
        request.user = self.superuser
        self.assertTrue(self.permission.has_permission(request, None))

    def test_regular_user_denied_permission(self):
        request = self.factory.get("/")
        request.user = self.regular_user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_anonymous_user_denied_permission(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))


class AdminSerializersTestCase(TestCase):
    def setUp(self):
        self.asset = Asset.objects.create(
            status="PENDING",
            coordinates={"lat": 27.7, "lng": 85.3},
            maker="TestMaker",
            model_no="M123",
        )

    def test_admin_asset_serializer_contains_all_fields(self):
        serializer = AdminAssetSerializer(self.asset)
        data = serializer.data
        self.assertEqual(data["id"], self.asset.id)
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["maker"], "TestMaker")
        self.assertIn("coordinates", data)

    def test_admin_asset_stats_serializer(self):
        stats_data = {
            "total_assets": 10,
            "pending_count": 4,
            "correct_count": 5,
            "incorrect_count": 1,
            "maintenance_due_count": 2,
        }
        serializer = AdminAssetStatsSerializer(data=stats_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["total_assets"], 10)
