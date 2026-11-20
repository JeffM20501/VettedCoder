import uuid
from datetime import datetime, timezone
import pytest
from django.apps import apps
from django.db import IntegrityError, transaction


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_user_table_name__metadata__matches_spec_users():
    """User model db_table must be 'users' per spec."""
    user_model = apps.get_model("accounts", "User")
    assert user_model._meta.db_table == "users"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_user_pk__default__is_uuidv7_from_base_model():
    """User primary key must be UUIDv7 inherited from BaseModel."""
    user_model = apps.get_model("accounts", "User")
    user = user_model()
    assert isinstance(user.pk, uuid.UUID)
    assert user.pk.version == 7


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_user_email_unique__duplicate_active_case_insensitive__raises_integrity_error():
    """Email must be unique case-insensitively among active (non-deleted) users."""
    user_model = apps.get_model("accounts", "User")
    user_model.objects.create(username="u1", email="candidate@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            user_model.objects.create(username="u2", email="CANDIDATE@EXAMPLE.COM")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_user_email_unique__duplicate_after_soft_delete__allows_reuse():
    """Soft-deleted user email can be reused by a new user."""
    user_model = apps.get_model("accounts", "User")
    user1 = user_model.objects.create(username="u1", email="reused@example.com")
    user1.delete()  # soft delete
    user2 = user_model.objects.create(username="u2", email="reused@example.com")
    assert user2.pk is not None


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_user_password__save_user__is_stored_hashed_never_plaintext():
    """User passwords must never be stored in plaintext."""
    user_model = apps.get_model("accounts", "User")
    user = user_model.objects.create(username="pwuser", email="pw@example.com")
    user.set_password("SecretPass123!")
    user.save()
    raw = user_model.objects.filter(pk=user.pk).values_list("password", flat=True).first()
    assert raw != "SecretPass123!"
    assert raw.startswith("pbkdf2_") or raw.startswith("argon2") or raw.startswith("bcrypt")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_user_fields__required_columns__enforce_not_null():
    """Required user fields (email, password) must enforce NOT NULL constraints."""
    user_model = apps.get_model("accounts", "User")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            user_model.objects.create(username="nonull", email=None)


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_guest_profile_table_name__metadata__matches_spec_guest_profiles():
    """GuestProfile model db_table must be 'guest_profiles' per spec."""
    guest_model = apps.get_model("accounts", "GuestProfile")
    assert guest_model._meta.db_table == "guest_profiles"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_guest_profile_email_unique__duplicate_email__raises_integrity_error():
    """GuestProfile email must be unique."""
    guest_model = apps.get_model("accounts", "GuestProfile")
    guest_model.objects.create(email="guest@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            guest_model.objects.create(email="guest@example.com")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_guest_profile_linked_user__on_delete_user__sets_fk_to_null():
    """GuestProfile.linked_user must have on_delete=SET_NULL."""
    user_model = apps.get_model("accounts", "User")
    guest_model = apps.get_model("accounts", "GuestProfile")
    user = user_model.objects.create(username="guser", email="guser@example.com")
    guest = guest_model.objects.create(email="guest_link@example.com", linked_user=user)
    user.delete()
    guest.refresh_from_db()
    assert guest.linked_user is None


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_user_auth_token_table_name__metadata__matches_spec_user_auth_tokens():
    """UserAuthToken model db_table must be 'user_auth_tokens' per spec."""
    token_model = apps.get_model("accounts", "UserAuthToken")
    assert token_model._meta.db_table == "user_auth_tokens"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_user_auth_token_purpose_check__invalid_purpose__raises_integrity_error():
    """UserAuthToken purpose must be constrained to verify_email or reset_password."""
    user_model = apps.get_model("accounts", "User")
    token_model = apps.get_model("accounts", "UserAuthToken")
    user = user_model.objects.create(username="u_auth", email="u_auth@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            token_model.objects.create(
                user=user,
                purpose="invalid_purpose",
                token_hash="hash123",
                expires_at=datetime.now(timezone.utc),
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_user_auth_token_hash_unique__duplicate_hash__raises_integrity_error():
    """UserAuthToken token_hash must be globally unique."""
    user_model = apps.get_model("accounts", "User")
    token_model = apps.get_model("accounts", "UserAuthToken")
    user = user_model.objects.create(username="u_hash", email="u_hash@example.com")
    token_model.objects.create(
        user=user,
        purpose="verify_email",
        token_hash="unique_hash_1",
        expires_at=datetime.now(timezone.utc),
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            token_model.objects.create(
                user=user,
                purpose="reset_password",
                token_hash="unique_hash_1",
                expires_at=datetime.now(timezone.utc),
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_user_auth_token_user_fk__on_delete_user__cascades():
    """UserAuthToken must CASCADE when user is deleted."""
    user_model = apps.get_model("accounts", "User")
    token_model = apps.get_model("accounts", "UserAuthToken")
    user = user_model.objects.create(username="u_casc", email="u_casc@example.com")
    token = token_model.objects.create(
        user=user,
        purpose="verify_email",
        token_hash="hash_casc",
        expires_at=datetime.now(timezone.utc),
    )
    user.delete()
    assert not token_model.objects.filter(pk=token.pk).exists()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_refresh_token_table_name__metadata__matches_spec_refresh_tokens():
    """RefreshToken model db_table must be 'refresh_tokens' per spec."""
    token_model = apps.get_model("accounts", "RefreshToken")
    assert token_model._meta.db_table == "refresh_tokens"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_refresh_token_hash_unique__duplicate_hash__raises_integrity_error():
    """RefreshToken token_hash must be unique."""
    user_model = apps.get_model("accounts", "User")
    token_model = apps.get_model("accounts", "RefreshToken")
    user = user_model.objects.create(username="u_rf", email="u_rf@example.com")
    fam = uuid.uuid7()
    token_model.objects.create(
        user=user,
        family_id=fam,
        token_hash="rf_hash_1",
        expires_at=datetime.now(timezone.utc),
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            token_model.objects.create(
                user=user,
                family_id=fam,
                token_hash="rf_hash_1",
                expires_at=datetime.now(timezone.utc),
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_refresh_token_user_fk__on_delete_user__cascades():
    """RefreshToken must CASCADE when user is deleted."""
    user_model = apps.get_model("accounts", "User")
    token_model = apps.get_model("accounts", "RefreshToken")
    user = user_model.objects.create(username="u_rfc", email="u_rfc@example.com")
    token = token_model.objects.create(
        user=user,
        family_id=uuid.uuid7(),
        token_hash="rf_casc_hash",
        expires_at=datetime.now(timezone.utc),
    )
    user.delete()
    assert not token_model.objects.filter(pk=token.pk).exists()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_refresh_token_replaced_by__on_delete_parent__sets_null():
    """RefreshToken replaced_by must set NULL when the predecessor token is deleted."""
    user_model = apps.get_model("accounts", "User")
    token_model = apps.get_model("accounts", "RefreshToken")
    user = user_model.objects.create(username="u_repl", email="u_repl@example.com")
    fam = uuid.uuid7()
    tok1 = token_model.objects.create(
        user=user, family_id=fam, token_hash="h1", expires_at=datetime.now(timezone.utc)
    )
    tok2 = token_model.objects.create(
        user=user,
        family_id=fam,
        token_hash="h2",
        replaced_by=tok1,
        expires_at=datetime.now(timezone.utc),
    )
    tok1.delete()
    tok2.refresh_from_db()
    assert tok2.replaced_by is None
