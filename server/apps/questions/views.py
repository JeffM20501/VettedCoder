from rest_framework.generics import ListAPIView
from .model import Questions
from apps.core.pagination import VettedCursorPagination
from .serializers import QuestionSerlializer


class QuestionViewSet(ListAPIView):
    queryset=Questions.objects.all()
    pagination_class = VettedCursorPagination
    serializer_class=QuestionSerlializer