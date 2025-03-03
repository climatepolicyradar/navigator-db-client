from datetime import datetime, timedelta, timezone

from db_client.models.dfce.family import (
    EventStatus,
    Family,
    FamilyCategory,
    FamilyEvent,
)


def test_calculates_last_updated_dates_based_on_latest_family_event(test_db):
    family_data = Family(
        import_id="family_import_id_1",
        title="Test Family Title",
        description="Test Family Description",
        family_category=FamilyCategory.EXECUTIVE,
    )

    test_db.add(family_data)
    test_db.commit()

    approved_event_date = datetime.now(tz=timezone.utc) - timedelta(
        days=365
    )  # 1 year ago
    passed_event_date = datetime.now(tz=timezone.utc) - timedelta(
        days=180
    )  # 6 months ago

    approved_event = FamilyEvent(
        import_id="event_import_id_1",
        title="Event Title Approved",
        date=approved_event_date,
        family_import_id=family_data.import_id,
        status=EventStatus.OK,
        event_type_name="Approved",
    )

    passed_event = FamilyEvent(
        import_id="event_import_id_2",
        title="Event Title Passed",
        date=passed_event_date,
        family_import_id=family_data.import_id,
        status=EventStatus.OK,
        event_type_name="Passed",
    )

    test_db.add(approved_event)
    test_db.add(passed_event)
    test_db.commit()

    families = test_db.query(Family).all()
    assert len(families) == 1

    family = families[0]

    assert len(family.events) == 2
    assert families[0].last_updated_date == passed_event_date


def test_family_last_updated_date_excludes_event_dates_in_the_future(test_db):

    family_data = Family(
        import_id="family_import_id_1",
        title="Test Family Title",
        description="Test Family Description",
        family_category=FamilyCategory.EXECUTIVE,
    )

    test_db.add(family_data)
    test_db.commit()

    approved_event_date = datetime.now(tz=timezone.utc) - timedelta(days=365)
    passed_event_date = datetime.now(tz=timezone.utc) - timedelta(days=180)
    future_completed_date = datetime.now(tz=timezone.utc) + timedelta(days=365)

    approved_event = FamilyEvent(
        import_id="event_import_id_1",
        title="Event Title Approved",
        date=approved_event_date,
        family_import_id=family_data.import_id,
        status=EventStatus.OK,
        event_type_name="Approved",
    )

    passed_event = FamilyEvent(
        import_id="event_import_id_2",
        title="Event Title Passed",
        date=passed_event_date,
        family_import_id=family_data.import_id,
        status=EventStatus.OK,
        event_type_name="Passed",
    )

    future_completed_event = FamilyEvent(
        import_id="event_import_id_3",
        title="Event Title Completed",
        date=future_completed_date,
        family_import_id=family_data.import_id,
        status=EventStatus.OK,
        event_type_name="Completed",
    )

    test_db.add(approved_event)
    test_db.add(passed_event)
    test_db.add(future_completed_event)
    test_db.commit()

    families = test_db.query(Family).all()
    assert len(families) == 1

    family = families[0]

    assert len(families) == 1
    assert len(family.events) == 3
    assert family.last_updated_date == passed_event_date
