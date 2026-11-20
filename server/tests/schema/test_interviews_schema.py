from datetime import datetime, timedelta, timezone
import pytest
from django.apps import apps
from django.db import IntegrityError, transaction


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_interview_session_table_name__metadata__matches_spec_sessions():
    """InterviewSession model db_table must be 'sessions' per spec."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    assert sess_model._meta.db_table == "sessions"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_interview_session_public_id_unique__duplicate_public_id__raises_integrity_error():
    """InterviewSession public_id must be globally unique."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    org_model = apps.get_model("organizations", "Organization")
    org = org_model.objects.create(name="Org Sess", slug="org-sess")

    sess_model.objects.create(
        organization=org,
        public_id="vetted-dup123",
        status="scheduled",
        session_type="interview",
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sess_model.objects.create(
                organization=org,
                public_id="vetted-dup123",
                status="scheduled",
                session_type="interview",
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_interview_session_status_check__invalid_status__raises_integrity_error():
    """Status must be in scheduled, waiting, active, completed, cancelled, expired, archived."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    org_model = apps.get_model("organizations", "Organization")
    org = org_model.objects.create(name="Org Bad Status", slug="org-bad-status")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sess_model.objects.create(
                organization=org,
                public_id="vetted-stat1",
                status="in_limbo",
                session_type="interview",
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_interview_session_type_check__invalid_type__raises_integrity_error():
    """session_type must be in interview, mock_interview, pair_programming, mentoring, practice."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    org_model = apps.get_model("organizations", "Organization")
    org = org_model.objects.create(name="Org Bad Type", slug="org-bad-type")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sess_model.objects.create(
                organization=org,
                public_id="vetted-type1",
                status="scheduled",
                session_type="hackathon",
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_interview_session_schedule_check__end_at_before_start_at__raises_integrity_error():
    """scheduled_end_at must be strictly greater than scheduled_start_at."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    org_model = apps.get_model("organizations", "Organization")
    org = org_model.objects.create(name="Org Sched Check", slug="org-sched-chk")

    now_utc = datetime.now(timezone.utc)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sess_model.objects.create(
                organization=org,
                public_id="vetted-sched1",
                status="scheduled",
                session_type="interview",
                scheduled_start_at=now_utc,
                scheduled_end_at=now_utc - timedelta(hours=1),
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_interview_session_timing_check__ended_at_before_started_at__raises_integrity_error():
    """ended_at must be >= started_at."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    org_model = apps.get_model("organizations", "Organization")
    org = org_model.objects.create(name="Org Timing Check", slug="org-timing-chk")

    now_utc = datetime.now(timezone.utc)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sess_model.objects.create(
                organization=org,
                public_id="vetted-time1",
                status="completed",
                session_type="interview",
                started_at=now_utc,
                ended_at=now_utc - timedelta(minutes=5),
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_interview_session_started_at__on_create__is_null_with_no_default():
    """started_at must have no default and remain NULL until interview is started."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    org_model = apps.get_model("organizations", "Organization")
    org = org_model.objects.create(name="Org Start Null", slug="org-start-null")

    sess = sess_model.objects.create(
        organization=org,
        public_id="vetted-nullstart",
        status="scheduled",
        session_type="interview",
    )
    assert sess.started_at is None


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_interview_session_org_fk__on_delete_organization__restricts_deletion():
    """Organization deletion is RESTRICTed when interview sessions exist."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    org_model = apps.get_model("organizations", "Organization")
    org = org_model.objects.create(name="Org Sess Restrict", slug="org-sess-restr")

    sess_model.objects.create(
        organization=org,
        public_id="vetted-restr1",
        status="scheduled",
        session_type="interview",
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            org.delete()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_session_participant_table_name__metadata__matches_spec_session_participants():
    """SessionParticipant model db_table must be 'session_participants'."""
    part_model = apps.get_model("interviews", "SessionParticipant")
    assert part_model._meta.db_table == "session_participants"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_participant_role_check__invalid_role__raises_integrity_error():
    """SessionParticipant role must be interviewer, co_interviewer, observer, or candidate."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    part_model = apps.get_model("interviews", "SessionParticipant")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Part", slug="org-part")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-part1", status="scheduled", session_type="interview"
    )
    user = user_model.objects.create(username="p_user", email="p_user@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            part_model.objects.create(session=sess, user=user, role="hacker")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_participant_identity_check__both_user_and_guest_set__raises_integrity_error():
    """SessionParticipant must enforce exactly one of user or guest_profile set."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    part_model = apps.get_model("interviews", "SessionParticipant")
    user_model = apps.get_model("accounts", "User")
    guest_model = apps.get_model("accounts", "GuestProfile")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Both", slug="org-both")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-both1", status="scheduled", session_type="interview"
    )
    user = user_model.objects.create(username="p_both", email="p_both@example.com")
    guest = guest_model.objects.create(email="guest_both@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            part_model.objects.create(session=sess, user=user, guest_profile=guest, role="candidate")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_participant_identity_check__neither_user_nor_guest_set__raises_integrity_error():
    """SessionParticipant must enforce at least one identity is set."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    part_model = apps.get_model("interviews", "SessionParticipant")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org None", slug="org-none")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-none1", status="scheduled", session_type="interview"
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            part_model.objects.create(
                session=sess, user=None, guest_profile=None, role="candidate"
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_participant_unique__duplicate_session_and_user__raises_integrity_error():
    """(session, user) must be unique in SessionParticipant."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    part_model = apps.get_model("interviews", "SessionParticipant")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Dup User", slug="org-dup-u")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-dupu", status="scheduled", session_type="interview"
    )
    user = user_model.objects.create(username="p_dupu", email="p_dupu@example.com")
    part_model.objects.create(session=sess, user=user, role="interviewer")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            part_model.objects.create(session=sess, user=user, role="observer")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_participant_unique__duplicate_session_and_guest__raises_integrity_error():
    """(session, guest_profile) must be unique in SessionParticipant."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    part_model = apps.get_model("interviews", "SessionParticipant")
    guest_model = apps.get_model("accounts", "GuestProfile")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Dup Guest", slug="org-dup-g")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-dupg", status="scheduled", session_type="interview"
    )
    guest = guest_model.objects.create(email="guest_dup@example.com")
    part_model.objects.create(session=sess, guest_profile=guest, role="candidate")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            part_model.objects.create(session=sess, guest_profile=guest, role="observer")


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_participant_session_fk__on_delete_session__cascades():
    """SessionParticipant must CASCADE when session is deleted."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    part_model = apps.get_model("interviews", "SessionParticipant")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Casc Part", slug="org-casc-part")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-cascpart", status="scheduled", session_type="interview"
    )
    user = user_model.objects.create(username="p_casc", email="p_casc@example.com")
    part = part_model.objects.create(session=sess, user=user, role="interviewer")
    sess.delete()
    assert not part_model.objects.filter(pk=part.pk).exists()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_candidate_access_token_table_name__metadata__matches_spec_candidate_access_tokens():
    """CandidateAccessToken model db_table must be 'candidate_access_tokens'."""
    cat_model = apps.get_model("interviews", "CandidateAccessToken")
    assert cat_model._meta.db_table == "candidate_access_tokens"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_candidate_access_token_hash_unique__duplicate_token_hash__raises_integrity_error():
    """CandidateAccessToken token_hash must be unique."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    part_model = apps.get_model("interviews", "SessionParticipant")
    cat_model = apps.get_model("interviews", "CandidateAccessToken")
    guest_model = apps.get_model("accounts", "GuestProfile")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Cat Hash", slug="org-cat-hash")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-cathash", status="scheduled", session_type="interview"
    )
    guest = guest_model.objects.create(email="cat_guest@example.com")
    part = part_model.objects.create(session=sess, guest_profile=guest, role="candidate")

    cat_model.objects.create(
        session=sess,
        participant=part,
        token_hash="cat_hash_123",
        expires_at=datetime.now(timezone.utc),
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            cat_model.objects.create(
                session=sess,
                participant=part,
                token_hash="cat_hash_123",
                expires_at=datetime.now(timezone.utc),
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_candidate_access_token_fks__on_delete_session_or_participant__cascades():
    """CandidateAccessToken must CASCADE when session or participant is deleted."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    part_model = apps.get_model("interviews", "SessionParticipant")
    cat_model = apps.get_model("interviews", "CandidateAccessToken")
    guest_model = apps.get_model("accounts", "GuestProfile")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Cat Casc", slug="org-cat-casc")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-catcasc", status="scheduled", session_type="interview"
    )
    guest = guest_model.objects.create(email="cat_casc@example.com")
    part = part_model.objects.create(session=sess, guest_profile=guest, role="candidate")
    tok = cat_model.objects.create(
        session=sess,
        participant=part,
        token_hash="cat_casc_h",
        expires_at=datetime.now(timezone.utc),
    )
    part.delete()
    assert not cat_model.objects.filter(pk=tok.pk).exists()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_question_unique__duplicate_session_and_position__raises_integrity_error():
    """(session, position) must be unique in SessionQuestion."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    sq_model = apps.get_model("interviews", "SessionQuestion")
    q_model = apps.get_model("questions", "Question")
    qv_model = apps.get_model("questions", "QuestionVersion")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    creator = user_model.objects.create(username="sq_u", email="sq_u@example.com")
    org = org_model.objects.create(name="Org SQ", slug="org-sq")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-sq1", status="scheduled", session_type="interview"
    )
    q1 = q_model.objects.create(
        title="SQ 1", slug="sq-1", visibility="global", difficulty="easy", created_by=creator
    )
    q2 = q_model.objects.create(
        title="SQ 2", slug="sq-2", visibility="global", difficulty="easy", created_by=creator
    )
    qv1 = qv_model.objects.create(
        question=q1, version=1, test_cases={"schema_version": 1}, languages=["python"]
    )
    qv2 = qv_model.objects.create(
        question=q2, version=1, test_cases={"schema_version": 1}, languages=["python"]
    )

    sq_model.objects.create(session=sess, question=q1, question_version=qv1, position=1)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sq_model.objects.create(session=sess, question=q2, question_version=qv2, position=1)


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_question_unique__duplicate_session_and_question__raises_integrity_error():
    """(session, question) must be unique in SessionQuestion."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    sq_model = apps.get_model("interviews", "SessionQuestion")
    q_model = apps.get_model("questions", "Question")
    qv_model = apps.get_model("questions", "QuestionVersion")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    creator = user_model.objects.create(username="sq_u2", email="sq_u2@example.com")
    org = org_model.objects.create(name="Org SQ2", slug="org-sq2")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-sq2", status="scheduled", session_type="interview"
    )
    q = q_model.objects.create(
        title="SQ Same", slug="sq-same", visibility="global", difficulty="easy", created_by=creator
    )
    qv = qv_model.objects.create(
        question=q, version=1, test_cases={"schema_version": 1}, languages=["python"]
    )

    sq_model.objects.create(session=sess, question=q, question_version=qv, position=1)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sq_model.objects.create(session=sess, question=q, question_version=qv, position=2)


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_session_question_pins_version__on_update_question_current_version__preserves_pinned_version():
    """SessionQuestion must pin specific QuestionVersion; future edits must not alter session version."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    sq_model = apps.get_model("interviews", "SessionQuestion")
    q_model = apps.get_model("questions", "Question")
    qv_model = apps.get_model("questions", "QuestionVersion")
    user_model = apps.get_model("accounts", "User")
    org_model = apps.get_model("organizations", "Organization")

    creator = user_model.objects.create(username="sq_pin", email="sq_pin@example.com")
    org = org_model.objects.create(name="Org Pin", slug="org-pin")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-pin1", status="scheduled", session_type="interview"
    )
    q = q_model.objects.create(
        title="Pin Q", slug="pin-q", visibility="global", difficulty="easy", created_by=creator
    )
    qv1 = qv_model.objects.create(
        question=q, version=1, test_cases={"schema_version": 1}, languages=["python"]
    )
    sq = sq_model.objects.create(session=sess, question=q, question_version=qv1, position=1)

    qv2 = qv_model.objects.create(
        question=q, version=2, test_cases={"schema_version": 1}, languages=["python"]
    )
    q.current_version = qv2
    q.save()

    sq.refresh_from_db()
    assert sq.question_version_id == qv1.pk
    assert sq.question_version.version == 1


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_file_unique__duplicate_session_and_path__raises_integrity_error():
    """(session, path) must be unique in SessionFile."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    sf_model = apps.get_model("interviews", "SessionFile")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org SF", slug="org-sf")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-sf1", status="scheduled", session_type="interview"
    )
    sf_model.objects.create(session=sess, path="main.py", language="python", content="print('hi')")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sf_model.objects.create(
                session=sess, path="main.py", language="python", content="print('bye')"
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_session_file_language_check__invalid_language__raises_integrity_error():
    """SessionFile language must be python, javascript, or typescript."""
    sess_model = apps.get_model("interviews", "InterviewSession")
    sf_model = apps.get_model("interviews", "SessionFile")
    org_model = apps.get_model("organizations", "Organization")

    org = org_model.objects.create(name="Org Bad Lang", slug="org-bad-lang")
    sess = sess_model.objects.create(
        organization=org, public_id="vetted-lang1", status="scheduled", session_type="interview"
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            sf_model.objects.create(
                session=sess, path="app.rb", language="ruby", content="puts 'hi'"
            )
