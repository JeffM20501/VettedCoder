from django.urls import path, include
from .views import QuestionViewSet


urlpatterns = [
    path("", QuestionViewSet.as_view(), name="questions")
]
