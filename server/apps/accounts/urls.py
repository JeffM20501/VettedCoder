from django.urls import path, include
from .views import MeView, RegisterView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("register/", RegisterView.as_view(), name='register')
]
