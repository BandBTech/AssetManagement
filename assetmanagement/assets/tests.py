from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from assets.models import Asset


class AssetUpdateAPITestCase(APITestCase):
    def setUp(self):
        self.asset = Asset.objects.create(
            original_image="uploads/originals/test.jpg",
            label="refrigerator",
            conf=0.95,
            coordinates={"lat": 100, "lng": 200},
            status="PENDING"
        )
        self.url = reverse("asset-detail", kwargs={"pk": self.asset.pk})

    def test_update_asset_details(self):
        payload = {
            "status": "CORRECT",
            "maker": "Samsung",
            "model_no": "sams4345",
            "year": 2012,
            "price_jpy": "567.56",
            "size": "512*512",
            "maintenance_cycle": 365,
            "last_maintenance_date": "2026-08-09",
            "notes": "Regular maintenance schedule"
        }
        response = self.client.patch(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response contains updated details and calculated next_maintenance_due
        self.assertEqual(response.data["status"], "CORRECT")
        self.assertEqual(response.data["maker"], "Samsung")
        self.assertEqual(response.data["model_no"], "sams4345")
        self.assertEqual(response.data["year"], 2012)
        self.assertEqual(float(response.data["price_jpy"]), 567.56)
        self.assertEqual(response.data["size"], "512*512")
        self.assertEqual(response.data["maintenance_cycle"], 365)
        self.assertEqual(response.data["last_maintenance_date"], "2026-08-09")
        self.assertEqual(response.data["next_maintenance_due"], "2027-08-09")

        # Verify database record is updated
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, "CORRECT")
        self.assertEqual(self.asset.maker, "Samsung")
        self.assertEqual(str(self.asset.next_maintenance_due), "2027-08-09")

