from rest_framework import serializers
from django.contrib.auth import get_user_model
from .validators import validate_email, validate_username
from django.contrib.auth.hashers import make_password

User=get_user_model()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields=["username", "created_at"]
        


class RegisterSerlizer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True, min_length=8)
    email=serializers.EmailField(required=True)
    
    class Meta:
        model=User
        fields=["id", "username", "email", "password"]
        read_only_fields=["id"]
        
    def validate_email(self, value):
        return validate_email(value)
    
    def validate_username(self,value):
        return validate_username(value)
    
    def create(self,validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=make_password(validated_data["password"])
        )