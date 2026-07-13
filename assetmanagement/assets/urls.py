from django.urls import path
from .views import AssetListCreateView, AssetRetrieveView, AssetFeedbackView

urlpatterns = [
    path("", AssetListCreateView.as_view(), name="asset-list-create"),
    path("<int:pk>/", AssetRetrieveView.as_view(), name="asset-detail"),
    path("<int:pk>/feedback/", AssetFeedbackView.as_view(), name="asset-feedback"),
]
