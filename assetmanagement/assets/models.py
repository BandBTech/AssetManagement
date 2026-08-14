from datetime import timedelta
from django.db import models
from django.utils.translation import gettext_lazy as _
from authentication.models import User


class Status(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CORRECT = "CORRECT", _("Correct")
    INCORRECT = "INCORRECT", _("Incorrect")

    

class Asset(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assets")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    original_image = models.ImageField(upload_to="uploads/originals/")
    predicted_image = models.ImageField(
        upload_to="uploads/predicted/", blank=True, null=True
    )
    label = models.JSONField(blank=True, null=True)
    conf = models.JSONField(blank=True, null=True)
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
    coordinates = models.JSONField()
    
    class Meta:
        ordering = ["-created_at"]  # newest first always

    def save(self, *args, **kwargs):
        if self.last_maintenance_date and self.maintenance_cycle:
            self.next_maintenance_due = self.last_maintenance_date + timedelta(days=self.maintenance_cycle)
        super().save(*args, **kwargs)

    def __str__(self):  
        return f"{self.label} - {self.status}"
