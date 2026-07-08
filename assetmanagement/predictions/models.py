from django.db import models
from django.utils.translation import gettext_lazy as _


class Status(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CORRECT = "CORRECT", _("Correct")
    INCORRECT = "INCORRECT", _("Incorrect")


class Prediction(models.Model):
    original_image = models.ImageField(upload_to="uploads/originals/")
    predicted_image = models.ImageField(
        upload_to="uploads/predicted/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    detected_objects = models.JSONField(blank=True, null=True, default=list)

    class Meta:
        ordering = ["-created_at"]  # newest first always

    def __str__(self):
        return f"{self.id} - {self.status}"
