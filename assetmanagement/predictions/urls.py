from django.urls import path
from .views import PredictAPIView, PredictionListView, PredictionRetrieveView, PredictionFeedback

urlpatterns = [
    path("", PredictionListView.as_view(), name="prediction-list"),
    path("<int:pk>/", PredictionRetrieveView.as_view(), name="prediction-detail"),
    path("predict/", PredictAPIView.as_view(), name="predict"),
    path("feedback/<int:pk>/", PredictionFeedback.as_view(), name="prediction-feedback"),
]
