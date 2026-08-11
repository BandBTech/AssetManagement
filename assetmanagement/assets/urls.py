from django.urls import path
from .views import AssetListCreateView, AssetRetrieveUpdateView, AssetFeedbackView

urlpatterns = [
    path("", AssetListCreateView.as_view(), name="asset-list-create"),
    path("<int:pk>/", AssetRetrieveUpdateView.as_view(), name="asset-detail"),
    path("<int:pk>/feedback/", AssetFeedbackView.as_view(), name="asset-feedback"),
]
