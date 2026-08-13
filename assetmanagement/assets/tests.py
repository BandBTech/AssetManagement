import io
from PIL import Image
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from assets.models import Asset
from assets.serializers import (
    AssetCreateSerializer,
    AssetDetailsAddSerializer,
    AssetRetrieveSerializer,
)

User = get_user_model()


def generate_test_image(filename="test.jpg"):
    file = io.BytesIO()
    img = Image.new("RGB", (10, 10), color="red")
    img.save(file, "jpeg")
    file.seek(0)
    return SimpleUploadedFile(filename, file.read(), content_type="image/jpeg")


class AssetCreateSerializerTestCase(APITestCase):
    def test_valid_creation(self):
        test_image = generate_test_image()
        payload = {"coordinates": {"lat": 27.700769, "lng": 85.300140}, "image": test_image}
        serializer = AssetCreateSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        asset = serializer.save()

        self.assertEqual(asset.coordinates, {"lat": 27.700769, "lng": 85.300140})
        self.assertEqual(asset.status, "PENDING")
        self.assertTrue(getattr(asset, "is_newly_created", False))

    def test_missing_image_fails(self):
        payload = {"coordinates": {"lat": 27.700769, "lng": 85.300140}}
        serializer = AssetCreateSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("image", serializer.errors)

    def test_missing_coordinates_fails(self):
        test_image = generate_test_image()
        payload = {"image": test_image}
        serializer = AssetCreateSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)

    def test_coordinates_not_dict_fails(self):
        payload = {"coordinates": "invalid_string_coordinates"}
        serializer = AssetCreateSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)

    def test_coordinates_missing_keys_fails(self):
        payload = {"coordinates": {"lat": 27.700769}}
        serializer = AssetCreateSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)

    def test_coordinates_invalid_number_fails(self):
        payload = {"coordinates": {"lat": "invalid_num", "lng": 85.300140}}
        serializer = AssetCreateSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("coordinates", serializer.errors)

    def test_coordinates_extra_keys_discarded(self):
        test_image = generate_test_image()
        payload = {
            "coordinates": {"lat": 27.700769, "lng": 85.300140, "malicious": "extra"},
            "image": test_image,
        }
        serializer = AssetCreateSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["coordinates"], {"lat": 27.700769, "lng": 85.300140})

    def test_corrupt_image_bytes_fails(self):
        corrupt_file = SimpleUploadedFile("corrupt.jpg", b"INVALID_BYTES", content_type="image/jpeg")
        payload = {"coordinates": {"lat": 27.700769, "lng": 85.300140}, "image": corrupt_file}
        serializer = AssetCreateSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("image", serializer.errors)


class AssetDetailsAddSerializerTestCase(APITestCase):
    def setUp(self):
        self.asset = Asset.objects.create(
            original_image="uploads/originals/test.jpg",
            label="refrigerator",
            conf=0.95,
            coordinates={"lat": 10.0, "lng": 20.0},
            status="PENDING",
        )

    def test_valid_details_update(self):
        payload = {
            "status": "CORRECT",
            "maker": "Samsung",
            "model_no": "sams4345",
            "year": 2012,
            "price_jpy": "567.56",
            "size": "512*512",
            "maintenance_cycle": 365,
            "last_maintenance_date": "2026-08-09",
            "next_maintenance_due": "2027-08-09",
            "notes": "Regular maintenance schedule",
        }
        serializer = AssetDetailsAddSerializer(instance=self.asset, data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_asset = serializer.save()

        self.assertEqual(updated_asset.maker, "Samsung")
        self.assertEqual(updated_asset.model_no, "sams4345")
        self.assertEqual(updated_asset.year, 2012)
        self.assertEqual(float(updated_asset.price_jpy), 567.56)

    def test_missing_required_fields_fails(self):
        payload = {
            "status": "CORRECT",
            "maker": "Samsung",
            # Missing model_no, year, price_jpy, size, maintenance_cycle, last_maintenance_date
        }
        serializer = AssetDetailsAddSerializer(instance=self.asset, data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("model_no", serializer.errors)
        self.assertIn("price_jpy", serializer.errors)


class AssetRetrieveSerializerTestCase(APITestCase):
    def setUp(self):
        from datetime import date
        self.asset = Asset.objects.create(
            original_image="uploads/originals/test.jpg",
            predicted_image="uploads/predicted/test_pred.jpg",
            label="refrigerator",
            conf=0.98,
            coordinates={"lat": 27.7, "lng": 85.3},
            status="CORRECT",
            maker="LG",
            model_no="LG-9000",
            year=2021,
            price_jpy=125000.00,
            size="600x1800",
            maintenance_cycle=180,
            last_maintenance_date=date(2026, 1, 1),
            notes="Checked fine",
        )

    def test_retrieve_representation(self):
        serializer = AssetRetrieveSerializer(instance=self.asset)
        data = serializer.data
        self.assertEqual(data["id"], self.asset.id)
        self.assertEqual(data["maker"], "LG")
        self.assertEqual(data["model_no"], "LG-9000")
        self.assertEqual(data["label"], "refrigerator")
        self.assertEqual(data["coordinates"], {"lat": 27.7, "lng": 85.3})


class AssetAPIEndpointsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="api_user", email="user@example.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)
        self.asset = Asset.objects.create(
            original_image="uploads/originals/test.jpg",
            label="refrigerator",
            conf=0.95,
            coordinates={"lat": 10.0, "lng": 20.0},
            status="PENDING",
        )

    def test_list_assets_endpoint_get(self):
        url = reverse("asset-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_asset_endpoint_post(self):
        url = reverse("asset-list-create")
        test_image = generate_test_image("post_test.jpg")
        payload = {
            "coordinates": '{"lat": 27.700769, "lng": 85.300140}',
            "image": test_image,
        }
        response = self.client.post(url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["status"], "PENDING")
        self.assertNotIn("maker", response.data)

    def test_create_or_retrieve_existing_asset_endpoint(self):
        from unittest.mock import patch
        url = reverse("asset-list-create")
        test_image1 = generate_test_image("post_dup1.jpg")
        payload = {
            "coordinates": '{"lat": 27.700769, "lng": 85.300140}',
            "image": test_image1,
        }
        with patch("assets.serializers.run_yolo_and_annotate") as mock_yolo:
            mock_yolo.return_value = ("uploads/predicted/test.jpg", {"label": "refrigerator", "confidence": 0.95})
            
            # First request -> 201 Created (AssetCreateSerializer - no maker/model_no fields)
            res1 = self.client.post(url, payload, format="multipart")
            self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
            self.assertTrue(res1.data["is_newly_created"])
            self.assertNotIn("maker", res1.data)

            # Second request -> 200 OK (AssetRetrieveSerializer - includes detail fields)
            test_image2 = generate_test_image("post_dup2.jpg")
            payload2 = {
                "coordinates": '{"lat": 27.700769, "lng": 85.300140}',
                "image": test_image2,
            }
            res2 = self.client.post(url, payload2, format="multipart")
            self.assertEqual(res2.status_code, status.HTTP_200_OK)
            self.assertFalse(res2.data["is_newly_created"])
            self.assertEqual(res2.data["id"], res1.data["id"])
            self.assertIn("maker", res2.data)


    def test_retrieve_asset_endpoint_get(self):
        url = reverse("asset-detail", kwargs={"pk": self.asset.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.asset.pk)
        self.assertEqual(response.data["label"], "refrigerator")

    def test_update_asset_endpoint_put_success(self):
        url = reverse("asset-detail", kwargs={"pk": self.asset.pk})
        payload = {
            "status": "CORRECT",
            "maker": "Samsung",
            "model_no": "sams4345",
            "year": 2012,
            "price_jpy": "567.56",
            "size": "512*512",
            "maintenance_cycle": 365,
            "last_maintenance_date": "2026-08-09",
            "next_maintenance_due": "2027-08-09",
            "notes": "Regular maintenance schedule",
        }
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["maker"], "Samsung")

        self.asset.refresh_from_db()
        self.assertEqual(self.asset.maker, "Samsung")

    def test_update_asset_endpoint_put_missing_fields_fails(self):
        url = reverse("asset-detail", kwargs={"pk": self.asset.pk})
        payload = {"maker": "Samsung"}
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_patch_asset_endpoint_disabled(self):
        url = reverse("asset-detail", kwargs={"pk": self.asset.pk})
        payload = {"maker": "Samsung"}
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrieve_non_existent_asset_404(self):
        url = reverse("asset-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_feedback_asset_endpoint_patch(self):
        url = reverse("asset-feedback", kwargs={"pk": self.asset.pk})
        payload = {"status": "INCORRECT"}
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "INCORRECT")

        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, "INCORRECT")
