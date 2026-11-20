import pytest
from django.apps import apps
from django.db import IntegrityError, transaction


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_question_table_name__metadata__matches_spec_questions():
    """Question model db_table must be 'questions' per spec."""
    q_model = apps.get_model("questions", "Question")
    assert q_model._meta.db_table == "questions"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_visibility_check__invalid_visibility__raises_integrity_error():
    """Question visibility must be in global, organization, or private."""
    q_model = apps.get_model("questions", "Question")
    user_model = apps.get_model("accounts", "User")
    creator = user_model.objects.create(username="q_u", email="q_u@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            q_model.objects.create(
                title="Q Title",
                slug="q-slug-bad-vis",
                visibility="invalid_vis",
                difficulty="medium",
                created_by=creator,
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_visibility_organization_check__organization_id_null__raises_integrity_error():
    """Visibility 'organization' requires organization_id to be non-NULL."""
    q_model = apps.get_model("questions", "Question")
    user_model = apps.get_model("accounts", "User")
    creator = user_model.objects.create(username="q_org_vis", email="q_org_vis@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            q_model.objects.create(
                title="Q Org Vis",
                slug="q-org-vis",
                visibility="organization",
                organization=None,
                difficulty="medium",
                created_by=creator,
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_visibility_global_check__organization_id_set__raises_integrity_error():
    """Visibility 'global' requires organization_id to be NULL."""
    q_model = apps.get_model("questions", "Question")
    org_model = apps.get_model("organizations", "Organization")
    user_model = apps.get_model("accounts", "User")

    creator = user_model.objects.create(username="q_glob", email="q_glob@example.com")
    org = org_model.objects.create(name="Org Glob", slug="org-glob")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            q_model.objects.create(
                title="Q Glob",
                slug="q-glob",
                visibility="global",
                organization=org,
                difficulty="medium",
                created_by=creator,
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_difficulty_check__invalid_difficulty__raises_integrity_error():
    """Question difficulty must be in easy, medium, or hard."""
    q_model = apps.get_model("questions", "Question")
    user_model = apps.get_model("accounts", "User")
    creator = user_model.objects.create(username="q_diff", email="q_diff@example.com")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            q_model.objects.create(
                title="Q Diff",
                slug="q-diff",
                visibility="private",
                difficulty="expert",
                created_by=creator,
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_slug_unique__duplicate_in_same_org_scope__raises_integrity_error():
    """Slug must be unique within the same organization scope among active questions."""
    q_model = apps.get_model("questions", "Question")
    org_model = apps.get_model("organizations", "Organization")
    user_model = apps.get_model("accounts", "User")

    creator = user_model.objects.create(username="q_slug_org", email="q_slug_org@example.com")
    org = org_model.objects.create(name="Org Q", slug="org-q")
    q_model.objects.create(
        title="Q 1",
        slug="two-sum",
        visibility="organization",
        organization=org,
        difficulty="easy",
        created_by=creator,
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            q_model.objects.create(
                title="Q 2",
                slug="two-sum",
                visibility="organization",
                organization=org,
                difficulty="easy",
                created_by=creator,
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_slug_unique__duplicate_in_global_scope__raises_integrity_error():
    """Slug must be unique in global scope (where organization is NULL)."""
    q_model = apps.get_model("questions", "Question")
    user_model = apps.get_model("accounts", "User")
    creator = user_model.objects.create(username="q_slug_glob", email="q_slug_glob@example.com")
    q_model.objects.create(
        title="Global Q 1",
        slug="fizz-buzz",
        visibility="global",
        organization=None,
        difficulty="easy",
        created_by=creator,
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            q_model.objects.create(
                title="Global Q 2",
                slug="fizz-buzz",
                visibility="global",
                organization=None,
                difficulty="easy",
                created_by=creator,
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_slug_unique__duplicate_after_soft_delete__allows_reuse():
    """Soft-deleted question slug can be reused."""
    q_model = apps.get_model("questions", "Question")
    user_model = apps.get_model("accounts", "User")
    creator = user_model.objects.create(username="q_reuse", email="q_reuse@example.com")
    q1 = q_model.objects.create(
        title="Q Del",
        slug="reused-q",
        visibility="global",
        organization=None,
        difficulty="easy",
        created_by=creator,
    )
    q1.delete()
    q2 = q_model.objects.create(
        title="Q New",
        slug="reused-q",
        visibility="global",
        organization=None,
        difficulty="easy",
        created_by=creator,
    )
    assert q2.pk is not None


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_created_by_fk__on_delete_user__restricts_deletion():
    """User deletion is RESTRICTed when the user has authored questions."""
    q_model = apps.get_model("questions", "Question")
    user_model = apps.get_model("accounts", "User")
    creator = user_model.objects.create(username="q_auth_del", email="q_auth_del@example.com")
    q_model.objects.create(
        title="Author Q",
        slug="author-q",
        visibility="global",
        organization=None,
        difficulty="medium",
        created_by=creator,
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            creator.delete()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_question_version_table_name__metadata__matches_spec_question_versions():
    """QuestionVersion model db_table must be 'question_versions'."""
    qv_model = apps.get_model("questions", "QuestionVersion")
    assert qv_model._meta.db_table == "question_versions"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_version_unique__duplicate_question_and_version__raises_integrity_error():
    """(question, version) must be unique."""
    q_model = apps.get_model("questions", "Question")
    qv_model = apps.get_model("questions", "QuestionVersion")
    user_model = apps.get_model("accounts", "User")

    creator = user_model.objects.create(username="qv_u", email="qv_u@example.com")
    q = q_model.objects.create(
        title="Ver Q", slug="ver-q", visibility="global", difficulty="easy", created_by=creator
    )
    qv_model.objects.create(
        question=q, version=1, test_cases={"schema_version": 1}, languages=["python"]
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            qv_model.objects.create(
                question=q, version=1, test_cases={"schema_version": 1}, languages=["python"]
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_version_number_check__zero_or_negative__raises_integrity_error():
    """QuestionVersion version number must be strictly positive (version > 0)."""
    q_model = apps.get_model("questions", "Question")
    qv_model = apps.get_model("questions", "QuestionVersion")
    user_model = apps.get_model("accounts", "User")

    creator = user_model.objects.create(username="qv_neg", email="qv_neg@example.com")
    q = q_model.objects.create(
        title="Ver Zero Q", slug="ver-zero-q", visibility="global", difficulty="easy", created_by=creator
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            qv_model.objects.create(
                question=q, version=0, test_cases={"schema_version": 1}, languages=["python"]
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_version_test_cases_check__non_object_json__raises_integrity_error():
    """QuestionVersion test_cases must be a JSON object, not a list or scalar."""
    q_model = apps.get_model("questions", "Question")
    qv_model = apps.get_model("questions", "QuestionVersion")
    user_model = apps.get_model("accounts", "User")

    creator = user_model.objects.create(username="qv_tc", email="qv_tc@example.com")
    q = q_model.objects.create(
        title="TC Q", slug="tc-q", visibility="global", difficulty="easy", created_by=creator
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            qv_model.objects.create(
                question=q, version=1, test_cases=["not", "an", "object"], languages=["python"]
            )


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_version_question_fk__on_delete_question__cascades():
    """QuestionVersion must CASCADE when question is deleted."""
    q_model = apps.get_model("questions", "Question")
    qv_model = apps.get_model("questions", "QuestionVersion")
    user_model = apps.get_model("accounts", "User")

    creator = user_model.objects.create(username="qv_casc", email="qv_casc@example.com")
    q = q_model.objects.create(
        title="Casc Q", slug="casc-q", visibility="global", difficulty="easy", created_by=creator
    )
    qv = qv_model.objects.create(
        question=q, version=1, test_cases={"schema_version": 1}, languages=["python"]
    )
    q.delete()
    assert not qv_model.objects.filter(pk=qv.pk).exists()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_question_current_version_circular_fk__deferred_in_transaction__allows_mutual_insert():
    """Question.current_version is a deferrable FK allowing mutual insert in transaction."""
    q_model = apps.get_model("questions", "Question")
    qv_model = apps.get_model("questions", "QuestionVersion")
    user_model = apps.get_model("accounts", "User")

    creator = user_model.objects.create(username="q_circ", email="q_circ@example.com")
    with transaction.atomic():
        q = q_model(
            title="Circ Q",
            slug="circ-q",
            visibility="global",
            difficulty="easy",
            created_by=creator,
        )
        qv = qv_model(
            question=q, version=1, test_cases={"schema_version": 1}, languages=["python"]
        )
        q.current_version = qv
        q.save()
        qv.save()

    q.refresh_from_db()
    assert q.current_version_id == qv.pk


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_interview_template_table_name__metadata__matches_spec_interview_templates():
    """InterviewTemplate model db_table must be 'interview_templates'."""
    tmpl_model = apps.get_model("questions", "InterviewTemplate")
    assert tmpl_model._meta.db_table == "interview_templates"


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_interview_template_question_unique__duplicate_template_and_position__raises_integrity_error():
    """(template, position) must be unique in InterviewTemplateQuestion."""
    tmpl_model = apps.get_model("questions", "InterviewTemplate")
    tq_model = apps.get_model("questions", "InterviewTemplateQuestion")
    q_model = apps.get_model("questions", "Question")
    user_model = apps.get_model("accounts", "User")

    creator = user_model.objects.create(username="tmpl_u", email="tmpl_u@example.com")
    q1 = q_model.objects.create(
        title="TQ 1", slug="tq-1", visibility="global", difficulty="easy", created_by=creator
    )
    q2 = q_model.objects.create(
        title="TQ 2", slug="tq-2", visibility="global", difficulty="easy", created_by=creator
    )
    tmpl = tmpl_model.objects.create(name="Standard Frontend Template", created_by=creator)
    tq_model.objects.create(template=tmpl, question=q1, position=1)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            tq_model.objects.create(template=tmpl, question=q2, position=1)


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_interview_template_question_fks__on_delete_rules__template_cascades_and_question_restricts():
    """Template deletion cascades items; Question deletion is restricted."""
    tmpl_model = apps.get_model("questions", "InterviewTemplate")
    tq_model = apps.get_model("questions", "InterviewTemplateQuestion")
    q_model = apps.get_model("questions", "Question")
    user_model = apps.get_model("accounts", "User")

    creator = user_model.objects.create(username="tq_del_u", email="tq_del_u@example.com")
    q = q_model.objects.create(
        title="TQ Del", slug="tq-del", visibility="global", difficulty="easy", created_by=creator
    )
    tmpl = tmpl_model.objects.create(name="Del Template", created_by=creator)
    tq = tq_model.objects.create(template=tmpl, question=q, position=1)

    # Deleting Question must be RESTRICTED
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            q.delete()

    # Deleting Template must CASCADE
    tmpl.delete()
    assert not tq_model.objects.filter(pk=tq.pk).exists()
