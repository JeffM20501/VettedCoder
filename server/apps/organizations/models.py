from django.db import models
from apps.core.models import BaseModel, SoftDeleteModel
from apps.organizations.validators import validate_retention_days
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import CheckConstraint,Q

MEMBER="member"
INTERVIEWER="interviewer"
ADMIN="admin"
OWNER="owner"

ROLES={
    ADMIN : "Admin",
    INTERVIEWER: "Interviewer",
    OWNER:"Owner",
    MEMBER: "Member",
}

def invitation_expires_at():
    return timezone.now() + timedelta(days=1)
class Organization(BaseModel):
    name=models.CharField(unique=True, blank=False)
    slug=models.SlugField(max_length=200, unique=True)
    retention_days=models.PositiveIntegerField(validators=[validate_retention_days], null=True)
    class Meta:
        db_table="organizations"
        constraints = [
            CheckConstraint(name="check_retention_days",condition=Q(retention_days__gt=0))
        ]

class OrganizationMembership(BaseModel):
    User=get_user_model()
    
    organization=models.ForeignKey(Organization, on_delete=models.RESTRICT)
    user=models.OneToOneField(User, on_delete=models.RESTRICT)
    role=models.CharField(max_length=15, choices=ROLES)
    class Meta:
        db_table="organization_memberships"
        constraints = [
                    CheckConstraint(name="check_role_membership",condition=Q(role="admin")  | Q(role="member") | Q(role="interviewer") | Q(role="owner"))
                ]
        
class Subscription(BaseModel):
    User=get_user_model()
    PRO="pro"
    FREE="free"
    
    PLAN={
        PRO:"Proffesional",
        FREE:"Free"
    }
    
    organization=models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)
    user=models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    plan_code=models.CharField(max_length=5, choices=PLAN, default=FREE)
    
    class Meta:
        db_table="subscriptions"
        constraints=[
            CheckConstraint(
                name="check_exact_one_set_user_org", 
                condition=
                    (Q(user__isnull=False)&Q(organization__isnull=True))
                        | 
                    (Q(user__isnull=True)&Q(user__isnull=False)))
        ]
        
class OrganizationInvitation(BaseModel):
    
    organization=models.ForeignKey(Organization, on_delete=models.CASCADE)
    email=models.EmailField(unique=True)
    role=models.CharField(max_length=15, choices=ROLES)
    token_hash=models.TextField(unique=True)
    expires_at=models.DateTimeField(default=invitation_expires_at)
    class Meta:
        db_table="organization_invitations"
        constraints = [
            CheckConstraint(name="check_role_invitation",condition=Q(role="admin")  | Q(role="member") | Q(role="interviewer"))
        ]