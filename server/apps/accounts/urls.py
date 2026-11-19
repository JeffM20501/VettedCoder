from django.urls import path, include
from .views import MeView

urlpatterns = [
    path("", MeView.as_view(), name="me")
]
