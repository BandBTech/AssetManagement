from django.db import models
from django.utils.translation import gettext_lazy as _


class Status(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CORRECT = "CORRECT", _("Correct")
    INCORRECT = "INCORRECT", _("Incorrect")


class Asset(models.Model):
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    original_image = models.ImageField(upload_to="uploads/originals/")
    predicted_image = models.ImageField(
        upload_to="uploads/predicted/", blank=True, null=True
    )
    
    label = models.JSONField(blank=True, null=True, default=list)
    conf = models.JSONField(blank=True, null=True, default=list)
    maker = models.CharField(max_length=255, blank=True, null=True)
    model_no = models.CharField(max_length=255, blank=True, null=True) 
    year = models.IntegerField(blank=True, null=True)
    price_jpy = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    size = models.CharField(max_length=255, blank=True, null=True)
    maintenance_cycle = models.IntegerField(blank=True, null=True, help_text="Maintenance cycle in days")
    last_maintenance_date = models.DateField(blank=True, null=True)
    next_maintenance_due = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    coordinates = models.JSONField(blank=True, null=True)
    
    
    class Meta:
        ordering = ["-created_at"]  # newest first always

    def __str__(self):  
        return f"{self.id} - {self.status}"
