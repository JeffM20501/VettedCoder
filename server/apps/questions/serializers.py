from rest_framework import serializers
from .model import Questions

class QuestionSerlializer(serializers.ModelSerializer):
    class Meta:
        model = Questions
        fields=["id", "title", "created_at"]