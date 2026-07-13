from django.db import models
from django.utils.translation import gettext_lazy as _


class Status(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CORRECT = "CORRECT", _("Correct")
    INCORRECT = "INCORRECT", _("Incorrect")


class Asset(models.Model):
    original_image = models.ImageField(upload_to="uploads/originals/")
    predicted_image = models.ImageField(
        upload_to="uploads/predicted/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    detected_objects = models.JSONField(blank=True, null=True, default=list)
    coordinates = models.JSONField(blank=True, null=True)
    
    # Additional data
    brand = models.CharField(max_length=255, blank=True, null=True)
    asset_model = models.CharField(max_length=255, blank=True, null=True) 
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    maintenance_period = models.IntegerField(blank=True, null=True, help_text="Maintenance period in days")

    class Meta:
        ordering = ["-created_at"]  # newest first always

    def __str__(self):  
        return f"{self.id} - {self.status}"
