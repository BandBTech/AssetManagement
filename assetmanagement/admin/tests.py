from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase
from base.permissions import IsSuperUser
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


class AdminAssetAPITestCase(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="adminuser", email="admin@example.com", password="password123"
        )
        self.regular_user = User.objects.create_user(
            username="normie", email="normie@example.com", password="password123"
        )
        self.asset1 = Asset.objects.create(
            status="PENDING",
            coordinates={"lat": 27.7, "lng": 85.3},
            maker="BrandA",
            model_no="M1",
            last_maintenance_date=date.today(),
            maintenance_cycle=10,
        )
        self.asset2 = Asset.objects.create(
            status="CORRECT",
            coordinates={"lat": 27.8, "lng": 85.4},
            maker="BrandB",
            model_no="M2",
        )
        self.list_url = reverse("admin-asset-list")
        self.stats_url = reverse("admin-asset-stats")

    def test_anonymous_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_access_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_list_assets(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(response.data, dict):
            results = response.data.get("results", response.data)
        else:
            results = response.data
        self.assertEqual(len(results), 2)

    def test_superuser_can_update_asset(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("admin-asset-detail", kwargs={"pk": self.asset1.pk})
        payload = {
            "status": "CORRECT",
            "maker": "BrandA_Updated",
            "coordinates": {"lat": 27.7, "lng": 85.3},
        }
        response = self.client.patch(detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.asset1.refresh_from_db()
        self.assertEqual(self.asset1.maker, "BrandA_Updated")
        self.assertEqual(self.asset1.status, "CORRECT")

    def test_superuser_can_delete_asset(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("admin-asset-detail", kwargs={"pk": self.asset1.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Asset.objects.filter(pk=self.asset1.pk).exists())

    def test_superuser_can_get_dashboard_stats(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_assets"], 2)
        self.assertEqual(response.data["pending_count"], 1)
        self.assertEqual(response.data["correct_count"], 1)
        self.assertEqual(response.data["incorrect_count"], 0)
        self.assertEqual(response.data["maintenance_due_count"], 1)

    def test_create_asset_disallowed(self):
        self.client.force_authenticate(user=self.superuser)
        payload = {
            "status": "PENDING",
            "maker": "NewMaker",
            "model_no": "M99",
            "coordinates": {"lat": 27.7, "lng": 85.3},
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AdminUserAPITestCase(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="adminuser", email="admin@example.com", password="password123"
        )
        self.regular_user = User.objects.create_user(
            username="normie", email="normie@example.com", password="password123"
        )
        self.target_user = User.objects.create_user(
            username="target", email="target@example.com", password="password123", first_name="Target", last_name="User"
        )
        self.list_url = reverse("admin-user-list")

    def test_anonymous_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_access_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_list_users(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 3)

    def test_superuser_can_create_user(self):
        self.client.force_authenticate(user=self.superuser)
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "first_name": "New",
            "last_name": "User",
            "is_staff": True,
            "is_superuser": False,
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username="newuser")
        self.assertTrue(new_user.check_password("securepassword123"))
        self.assertEqual(new_user.email, "newuser@example.com")
        self.assertTrue(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)

    def test_superuser_can_retrieve_user(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("admin-user-detail", kwargs={"pk": self.target_user.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "target")

    def test_superuser_can_update_user_without_password(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("admin-user-detail", kwargs={"pk": self.target_user.pk})
        payload = {"first_name": "UpdatedTarget"}
        response = self.client.patch(detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.first_name, "UpdatedTarget")
        self.assertTrue(self.target_user.check_password("password123"))

    def test_superuser_can_update_user_password(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("admin-user-detail", kwargs={"pk": self.target_user.pk})
        payload = {"password": "brandnewpassword"}
        response = self.client.patch(detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password("brandnewpassword"))

    def test_superuser_can_delete_user(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("admin-user-detail", kwargs={"pk": self.target_user.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.target_user.pk).exists())

    def test_admin_create_user_short_password_fails(self):
        self.client.force_authenticate(user=self.superuser)
        payload = {
            "username": "short_admin_user",
            "email": "shortadmin@example.com",
            "password": "123",  # Less than min_length=8
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_update_user_duplicate_email_fails(self):
        self.client.force_authenticate(user=self.superuser)
        detail_url = reverse("admin-user-detail", kwargs={"pk": self.target_user.pk})
        payload = {"email": "admin@example.com"}  # Duplicate of superuser's email
        response = self.client.patch(detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



