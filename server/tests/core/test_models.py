import uuid
from datetime import UTC, datetime

import pytest
from django.db import models

pytestmark=pytest.mark.django_db

@pytest.mark.spec
@pytest.mark.unit
def test_uuidv7_pk__generated_in_app__is_time_sortable(clock):
    """
    All primary keys are UUIDv7, generated in the application.
    Tests assert time-sortability.
    """
    from apps.core.models import BaseModel

    class DummyUUIDModel(BaseModel):
        class Meta:
            app_label = "core"

        name = models.CharField(max_length=50)

    # Generate IDs across time intervals
    clock.set(datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC))
    id_1 = DummyUUIDModel().id
    clock.tick(1)
    id_2 = DummyUUIDModel().id
    clock.tick(5)
    id_3 = DummyUUIDModel().id

    assert isinstance(id_1, uuid.UUID)
    assert id_1.version == 7
    assert id_2.version == 7
    assert id_3.version == 7
    assert id_1 < id_2 < id_3


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_timestamps__model_create_and_update__sets_utc_timestamps_correctly(clock):
    """
    created_at is set once on create in UTC; updated_at monotonically advances on save.
    """
    from apps.core.models import BaseModel

    class DummyTimestampModel(BaseModel):
        class Meta:
            app_label = "core"

        title = models.CharField(max_length=100)

    start_time = datetime(2026, 3, 15, 12, 0, 0, tzinfo=UTC)
    clock.set(start_time)

    instance = DummyTimestampModel.objects.create(title="Initial")
    assert instance.created_at == start_time
    assert instance.updated_at == start_time

    # Advance clock and update
    clock.tick(30)
    later_time = datetime(2026, 3, 15, 12, 0, 30, tzinfo=UTC)
    instance.title = "Modified"
    instance.save()
    instance.refresh_from_db()

    assert instance.created_at == start_time
    assert instance.updated_at == later_time


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_soft_delete__record_deleted__hidden_from_default_manager():
    """
    Soft-delete manager hides deleted rows from standard queries.
    """
    from apps.core.models import SoftDeleteModel

    class DummySoftDeleteModel(SoftDeleteModel):
        class Meta:
            app_label = "core"

        name = models.CharField(max_length=50)

    item = DummySoftDeleteModel.objects.create(name="Active Item")
    item.delete()

    assert DummySoftDeleteModel.objects.filter(id=item.id).count() == 0
    assert not DummySoftDeleteModel.objects.filter(name="Active Item").exists()


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_soft_delete__with_deleted_manager__exposes_soft_deleted_records():
    """
    all_objects includes both active and soft-deleted rows.
    """
    from apps.core.models import SoftDeleteModel

    class DummySoftDeleteModel(SoftDeleteModel):
        class Meta:
            app_label = "core"

        name = models.CharField(max_length=50)

    active = DummySoftDeleteModel.objects.create(name="Keep Active")
    deleted = DummySoftDeleteModel.objects.create(name="Soft Delete Me")
    deleted.delete()

    all_records = DummySoftDeleteModel.all_objects.all()
    assert all_records.filter(id=active.id).exists()
    assert all_records.filter(id=deleted.id).exists()
    assert deleted.deleted_at is not None


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_soft_delete__restore__restores_record_to_default_manager():
    """
    Restoring a soft-deleted record clears deleted_at and surfaces it in Model.objects.
    """
    from apps.core.models import SoftDeleteModel

    class DummySoftDeleteModel(SoftDeleteModel):
        class Meta:
            app_label = "core"

        name = models.CharField(max_length=50)

    item = DummySoftDeleteModel.objects.create(name="To Restore")
    item.delete()
    assert DummySoftDeleteModel.objects.filter(id=item.id).count() == 0

    item.restore()
    assert item.deleted_at is None
    assert DummySoftDeleteModel.objects.filter(id=item.id).count() == 1


@pytest.mark.spec
@pytest.mark.integration
@pytest.mark.django_db
def test_hard_delete__explicit_deletion__permanently_removes_row_from_db():
    """
    hard_delete() removes row completely from the database table.
    """
    from apps.core.models import SoftDeleteModel

    class DummySoftDeleteModel(SoftDeleteModel):
        class Meta:
            app_label = "core"

        name = models.CharField(max_length=50)

    item = DummySoftDeleteModel.objects.create(name="Hard Delete Target")
    item.hard_delete()

    assert DummySoftDeleteModel.objects.filter(id=item.id).count() == 0
    assert DummySoftDeleteModel.all_objects.filter(id=item.id).count() == 0
