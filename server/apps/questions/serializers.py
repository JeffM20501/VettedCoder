from rest_framework import serializers
from .models import Questions

class QuestionSerlializer(serializers.ModelSerializer):
    class Meta:
        model = Questions
        fields=["id", "title", "created_at"]