from django.urls import path, include
from .views import OrgMembersView

urlpatterns = [
    path("", OrgMembersView.as_view(), name='org_members')
]

