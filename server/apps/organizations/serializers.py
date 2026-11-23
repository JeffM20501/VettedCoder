from rest_framework import serializers
from .models import Organizations


class OrganizationSerlizers(serializers.ModelSerializer):
    model = Organizations
    fields=["username", "created_at"]