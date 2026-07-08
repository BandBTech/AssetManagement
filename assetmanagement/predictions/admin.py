from django.contrib import admin
from .models import Prediction
from django.utils.html import format_html


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "predicted_image_preview", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id",)
    ordering = ("-created_at",)

    @admin.display(description="Predicted")
    def predicted_image_preview(self, obj):
        if obj.predicted_image and getattr(obj.predicted_image, "url", None):
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="100" height="100" style="object-fit: cover;"/></a>',
                obj.predicted_image.url,
                obj.predicted_image.url,
            )
        return "No Image"
