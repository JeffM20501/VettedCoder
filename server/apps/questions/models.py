from django.db import models
from apps.core.models import BaseModel

class Questions(BaseModel):
    
    class Meta:
        db_table="questions"