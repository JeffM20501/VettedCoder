import pytest
from django.apps import apps
from django.db import IntegrityError, transaction


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_scorecard_template_table_name__metadata__matches_spec_scorecard_templates():
    """ScorecardTemplate model db_table must be 'scorecard_templates'."""
    st_model = apps.get_model("evaluation", "ScorecardTemplate")
    assert st_model._meta.db_table == "scorecard_templates"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_scorecard_criterion_unique__duplicate_template_and_key__raises_integrity_error():
    """(template, key) must be unique in ScorecardCriterion."""
    st_model = apps.get_model("evaluation", "ScorecardTemplate")
    sc_model = apps.get_model("evaluation", "ScorecardCriterion")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Crit", slug="org-crit")
    tmpl = st_model.objects.create(organization=org, name="Eng Template")
    sc_model.objects.create(template=tmpl, key="problem_solving", title="Problem Solving", scale_min=1, scale_max=4)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sc_model.objects.create(
                template=tmpl, key="problem_solving", title="Another Criterion", scale_min=1, scale_max=4
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_scorecard_criterion_scale_check__scale_max_not_greater_than_min__raises_integrity_error():
    """ScorecardCriterion must enforce scale_max > scale_min."""
    st_model = apps.get_model("evaluation", "ScorecardTemplate")
    sc_model = apps.get_model("evaluation", "ScorecardCriterion")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Scale", slug="org-scale")
    tmpl = st_model.objects.create(organization=org, name="Scale Template")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sc_model.objects.create(
                template=tmpl, key="bad_scale", title="Bad Scale", scale_min=4, scale_max=2
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_scorecard_table_name__metadata__matches_spec_scorecards():
    """Scorecard model db_table must be 'scorecards'."""
    card_model = apps.get_model("evaluation", "Scorecard")
    assert card_model._meta.db_table == "scorecards"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_scorecard_unique__duplicate_author_per_session_active__raises_integrity_error():
    """(session, author) must be unique among active scorecards."""
    card_model = apps.get_model("evaluation", "Scorecard")
    sess_model = apps.get_model("interviews", "InterviewSession")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Card", slug="org-card")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-card1", status="active", session_type="interview"
    )
    author = user_model.objects.create(username="card_auth", email="card_auth@example.com")

    card_model.objects.create(session=sess, author=author, recommendation="hire", status="draft")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            card_model.objects.create(session=sess, author=author, recommendation="no_hire", status="draft")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_scorecard_recommendation_check__invalid_recommendation__raises_integrity_error():
    """Scorecard recommendation must be in strong_hire, hire, no_hire, strong_no_hire."""
    card_model = apps.get_model("evaluation", "Scorecard")
    sess_model = apps.get_model("interviews", "InterviewSession")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Rec", slug="org-rec")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-rec1", status="active", session_type="interview"
    )
    author = user_model.objects.create(username="rec_auth", email="rec_auth@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            card_model.objects.create(session=sess, author=author, recommendation="maybe", status="draft")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_scorecard_status_check__invalid_status__raises_integrity_error():
    """Scorecard status must be in draft, submitted."""
    card_model = apps.get_model("evaluation", "Scorecard")
    sess_model = apps.get_model("interviews", "InterviewSession")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Card Stat", slug="org-card-stat")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-statcard", status="active", session_type="interview"
    )
    author = user_model.objects.create(username="card_stat_auth", email="card_stat_auth@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            card_model.objects.create(session=sess, author=author, recommendation="hire", status="published")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_scorecard_fks__on_delete_session_cascades_and_author_restricts():
    """Session deletion cascades scorecards; Author deletion is restricted."""
    card_model = apps.get_model("evaluation", "Scorecard")
    sess_model = apps.get_model("interviews", "InterviewSession")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Card FK", slug="org-card-fk")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-cardfk", status="active", session_type="interview"
    )
    author = user_model.objects.create(username="card_fk_u", email="card_fk_u@example.com")
    card = card_model.objects.create(session=sess, author=author, recommendation="hire", status="draft")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            author.delete()

    sess.delete()
    assert not card_model.objects.filter(pk=card.pk).exists()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_scorecard_rating_unique__duplicate_scorecard_and_criterion__raises_integrity_error():
    """(scorecard, criterion) must be unique in ScorecardRating."""
    card_model = apps.get_model("evaluation", "Scorecard")
    rate_model = apps.get_model("evaluation", "ScorecardRating")
    st_model = apps.get_model("evaluation", "ScorecardTemplate")
    sc_model = apps.get_model("evaluation", "ScorecardCriterion")
    sess_model = apps.get_model("interviews", "InterviewSession")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Rate", slug="org-rate")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-rate1", status="active", session_type="interview"
    )
    author = user_model.objects.create(username="rate_auth", email="rate_auth@example.com")
    tmpl = st_model.objects.create(organization=org, name="Rate Tmpl")
    crit = sc_model.objects.create(template=tmpl, key="arch", title="Architecture", scale_min=1, scale_max=4)
    card = card_model.objects.create(session=sess, author=author, recommendation="hire", status="draft")

    rate_model.objects.create(scorecard=card, criterion=crit, score=3)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            rate_model.objects.create(scorecard=card, criterion=crit, score=4)


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_note_author_fk__on_delete_author__restricts_deletion():
    """User deletion is RESTRICTed when the user has authored session notes."""
    note_model = apps.get_model("evaluation", "SessionNote")
    sess_model = apps.get_model("interviews", "InterviewSession")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Note", slug="org-note")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-note1", status="active", session_type="interview"
    )
    author = user_model.objects.create(username="note_auth", email="note_auth@example.com")
    note_model.objects.create(session=sess, author=author, content="Private note")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            author.delete()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_session_artifact_table_name__metadata__matches_spec_session_artifacts():
    """SessionArtifact model db_table must be 'session_artifacts'."""
    art_model = apps.get_model("playback", "SessionArtifact")
    assert art_model._meta.db_table == "session_artifacts"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_artifact_type_check__invalid_type__raises_integrity_error():
    """artifact_type must be in playback_bundle, report, whiteboard_snapshot."""
    art_model = apps.get_model("playback", "SessionArtifact")
    sess_model = apps.get_model("interviews", "InterviewSession")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Art Type", slug="org-art-type")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-arttype", status="completed", session_type="interview"
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            art_model.objects.create(
                session=sess,
                artifact_type="raw_dump",
                status="pending",
                storage_key="sessions/123/bundle",
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_artifact_status_check__invalid_status__raises_integrity_error():
    """SessionArtifact status must be in pending, ready, failed."""
    art_model = apps.get_model("playback", "SessionArtifact")
    sess_model = apps.get_model("interviews", "InterviewSession")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Art Stat", slug="org-art-stat")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-artstat", status="completed", session_type="interview"
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            art_model.objects.create(
                session=sess,
                artifact_type="playback_bundle",
                status="processing",
                storage_key="sessions/123/bundle",
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_audit_log_table_name__metadata__matches_spec_audit_logs():
    """AuditLog model db_table must be 'audit_logs'."""
    audit_model = apps.get_model("audit", "AuditLog")
    assert audit_model._meta.db_table == "audit_logs"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_audit_log_immutability__attempt_update_or_delete__raises_integrity_error_or_is_prevented():
    """AuditLog is append-only; update and delete must be disallowed."""
    audit_model = apps.get_model("audit", "AuditLog")
    log = audit_model.objects.create(action="login", details={"ip": "127.0.0.1"})
    with pytest.raises((IntegrityError, RuntimeError, PermissionError)):
        with transaction.atomic():
            log.action = "tampered"
            log.save()
