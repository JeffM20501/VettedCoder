import subprocess
import sys
import pytest
from django.apps import apps
from apps.core.models import BaseModel, SoftDeleteModel

DOMAIN_APP_LABELS = [
    "accounts",
    "organizations",
    "questions",
    "interviews",
    "evaluation",
    "playback",
    "audit",
]

SOFT_DELETABLE_MODELS = {
    ("accounts", "User"),
    ("organizations", "Organization"),
    ("organizations", "OrganizationMembership"),
    ("questions", "Question"),
    ("interviews", "InterviewSession"),
    ("evaluation", "Scorecard"),
}


@pytest.mark.spec
@pytest.mark.integration
def test_models__all_domain_models__inherit_base_model_with_uuidv7_pk():
    """Every model across all domain apps must inherit BaseModel with UUIDv7 primary key."""
    found_any = False
    for app_label in DOMAIN_APP_LABELS:
        try:
            app_config = apps.get_app_config(app_label)
        except LookupError:
            pytest.fail(f"Required domain app '{app_label}' is not registered in INSTALLED_APPS.")

        for model in app_config.get_models():
            found_any = True
            assert issubclass(
                model, BaseModel
            ), f"Model '{model.__name__}' in app '{app_label}' does not inherit BaseModel."
            pk_field = model._meta.pk
            assert pk_field is not None
            assert pk_field.get_internal_type() == "UUIDField"

    assert found_any, "No domain models were discovered."


@pytest.mark.spec
@pytest.mark.integration
def test_models__soft_deletable_models__inherit_soft_delete_model():
    """All core soft-deletable entities must inherit SoftDeleteModel."""
    for app_label, model_name in SOFT_DELETABLE_MODELS:
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            pytest.fail(f"Required soft-deletable model '{model_name}' in app '{app_label}' is missing.")

        assert issubclass(
            model, SoftDeleteModel
        ), f"Model '{model_name}' in app '{app_label}' must inherit SoftDeleteModel."
        assert hasattr(model, "is_deleted")
        assert hasattr(model, "deleted_at")


@pytest.mark.spec
@pytest.mark.slow
@pytest.mark.integration
def test_migrations__apply_from_zero_and_unapply__reverses_cleanly():
    """Migrations must apply forward from zero and reverse cleanly."""
    res_zero = subprocess.run(
        [sys.executable, "manage.py", "migrate", "zero", "--noinput"],
        capture_output=True,
        text=True,
    )
    assert res_zero.returncode == 0, f"Failed reversing migrations: {res_zero.stderr}"

    res_fwd = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        capture_output=True,
        text=True,
    )
    assert res_fwd.returncode == 0, f"Failed applying migrations forward: {res_fwd.stderr}"


@pytest.mark.spec
@pytest.mark.integration
def test_migrations__makemigrations_check__reports_no_uncommitted_changes():
    """makemigrations --check must report clean with no unapplied/missing migrations."""
    res = subprocess.run(
        [sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Uncommitted model changes detected: {res.stdout}\n{res.stderr}"
