from datetime import datetime, timezone
import pytest
from django.apps import apps
from django.db import IntegrityError, transaction


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_organization_table_name__metadata__matches_spec_organizations():
    """Organization model db_table must be 'organizations' per spec."""
    org_model = apps.get_model("organizations", "Organization")
    assert org_model._meta.db_table == "organizations"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_slug_unique__duplicate_active_slug__raises_integrity_error():
    """Slug must be unique among active (non-deleted) organizations."""
    org_model = apps.get_model("organizations", "Organization")
    org_model.objects.create(name="Org One", slug="acme")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            org_model.objects.create(name="Org Two", slug="acme")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_slug_unique__duplicate_after_soft_delete__allows_reuse():
    """Soft-deleted organization slug can be reused."""
    org_model = apps.get_model("organizations", "Organization")
    org1 = org_model.objects.create(name="Org One", slug="reused-slug")
    org1.delete()  # soft delete
    org2 = org_model.objects.create(name="Org Two", slug="reused-slug")
    assert org2.pk is not None


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_retention_days_check__negative_or_zero__raises_integrity_error():
    """Organization retention_days must be strictly positive if set."""
    org_model = apps.get_model("organizations", "Organization")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            org_model.objects.create(name="Org Zero", slug="zero-ret", retention_days=0)


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_organization_membership_table_name__metadata__matches_spec_organization_memberships():
    """OrganizationMembership model db_table must be 'organization_memberships'."""
    mem_model = apps.get_model("organizations", "OrganizationMembership")
    assert mem_model._meta.db_table == "organization_memberships"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_membership_role_check__invalid_role__raises_integrity_error():
    """OrganizationMembership role must be owner, admin, interviewer, or member."""
    org_model = apps.get_model("organizations", "Organization")
    user_model = apps.get_model("accounts", "User")
    mem_model = apps.get_model("organizations", "OrganizationMembership")

    org = org_model.objects.create(name="Org Role", slug="org-role")
    user = user_model.objects.create(username="u_role", email="u_role@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            mem_model.objects.create(organization=org, user=user, role="invalid_role")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_membership_unique__duplicate_active_org_user__raises_integrity_error():
    """(organization, user) must be unique among active members."""
    org_model = apps.get_model("organizations", "Organization")
    user_model = apps.get_model("accounts", "User")
    mem_model = apps.get_model("organizations", "OrganizationMembership")

    org = org_model.objects.create(name="Org Dup", slug="org-dup")
    user = user_model.objects.create(username="u_dup", email="u_dup@example.com")
    mem_model.objects.create(organization=org, user=user, role="member")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            mem_model.objects.create(organization=org, user=user, role="admin")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_membership_unique__duplicate_after_soft_delete__allows_rejoin():
    """Soft-deleted membership can be recreated (user rejoins org)."""
    org_model = apps.get_model("organizations", "Organization")
    user_model = apps.get_model("accounts", "User")
    mem_model = apps.get_model("organizations", "OrganizationMembership")

    org = org_model.objects.create(name="Org Rejoin", slug="org-rejoin")
    user = user_model.objects.create(username="u_rejoin", email="u_rejoin@example.com")
    m1 = mem_model.objects.create(organization=org, user=user, role="member")
    m1.delete()
    m2 = mem_model.objects.create(organization=org, user=user, role="member")
    assert m2.pk is not None


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_membership_fk__on_delete_organization__restricts_deletion():
    """Organization deletion is RESTRICTed when members exist."""
    org_model = apps.get_model("organizations", "Organization")
    user_model = apps.get_model("accounts", "User")
    mem_model = apps.get_model("organizations", "OrganizationMembership")

    org = org_model.objects.create(name="Org Restrict", slug="org-restrict")
    user = user_model.objects.create(username="u_restr", email="u_restr@example.com")
    mem_model.objects.create(organization=org, user=user, role="owner")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            org.delete()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_membership_fk__on_delete_user__restricts_deletion():
    """User deletion is RESTRICTed when user has organization memberships."""
    org_model = apps.get_model("organizations", "Organization")
    user_model = apps.get_model("accounts", "User")
    mem_model = apps.get_model("organizations", "OrganizationMembership")

    org = org_model.objects.create(name="Org Restr User", slug="org-restr-user")
    user = user_model.objects.create(username="u_restr_u", email="u_restr_u@example.com")
    mem_model.objects.create(organization=org, user=user, role="member")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            user.delete()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_organization_invitation_table_name__metadata__matches_spec_organization_invitations():
    """OrganizationInvitation model db_table must be 'organization_invitations'."""
    inv_model = apps.get_model("organizations", "OrganizationInvitation")
    assert inv_model._meta.db_table == "organization_invitations"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_invitation_role_check__invalid_role__raises_integrity_error():
    """OrganizationInvitation role must be admin, interviewer, or member."""
    org_model = apps.get_model("organizations", "Organization")
    inv_model = apps.get_model("organizations", "OrganizationInvitation")
    org = org_model.objects.create(name="Org Inv Role", slug="org-inv-role")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            inv_model.objects.create(
                organization=org,
                email="invite@example.com",
                role="owner",  # owner cannot be invited
                token_hash="tok_inv_1",
                expires_at=datetime.now(timezone.utc),
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_invitation_token_hash_unique__duplicate_token_hash__raises_integrity_error():
    """OrganizationInvitation token_hash must be globally unique."""
    org_model = apps.get_model("organizations", "Organization")
    inv_model = apps.get_model("organizations", "OrganizationInvitation")
    org = org_model.objects.create(name="Org Inv Hash", slug="org-inv-hash")
    inv_model.objects.create(
        organization=org,
        email="inv1@example.com",
        role="member",
        token_hash="same_inv_hash",
        expires_at=datetime.now(timezone.utc),
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            inv_model.objects.create(
                organization=org,
                email="inv2@example.com",
                role="member",
                token_hash="same_inv_hash",
                expires_at=datetime.now(timezone.utc),
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_organization_invitation_org_fk__on_delete_organization__cascades():
    """OrganizationInvitation must CASCADE when organization is deleted."""
    org_model = apps.get_model("organizations", "Organization")
    inv_model = apps.get_model("organizations", "OrganizationInvitation")
    org = org_model.objects.create(name="Org Inv Casc", slug="org-inv-casc")
    inv = inv_model.objects.create(
        organization=org,
        email="casc@example.com",
        role="member",
        token_hash="casc_hash",
        expires_at=datetime.now(timezone.utc),
    )
    org.delete()
    assert not inv_model.objects.filter(pk=inv.pk).exists()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_subscription_table_name__metadata__matches_spec_subscriptions():
    """Subscription model db_table must be 'subscriptions' per spec."""
    sub_model = apps.get_model("organizations", "Subscription")
    assert sub_model._meta.db_table == "subscriptions"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_subscription_target_check__both_org_and_user_set__raises_integrity_error():
    """Subscription must enforce that exactly one of organization or user is set."""
    org_model = apps.get_model("organizations", "Organization")
    user_model = apps.get_model("accounts", "User")
    sub_model = apps.get_model("organizations", "Subscription")

    org = org_model.objects.create(name="Org Sub", slug="org-sub")
    user = user_model.objects.create(username="sub_u", email="sub_u@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sub_model.objects.create(organization=org, user=user, plan_code="pro")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_subscription_target_check__neither_org_nor_user_set__raises_integrity_error():
    """Subscription must enforce that at least one target is set (not both NULL)."""
    sub_model = apps.get_model("organizations", "Subscription")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sub_model.objects.create(organization=None, user=None, plan_code="pro")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_subscription_plan_code__default_value__is_free():
    """Subscription plan_code default must be 'free'."""
    org_model = apps.get_model("organizations", "Organization")
    sub_model = apps.get_model("organizations", "Subscription")
    org = org_model.objects.create(name="Org Free", slug="org-free")
    sub = sub_model(organization=org)
    assert sub.plan_code == "free"
