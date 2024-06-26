from sqlalchemy.orm import Session

from db_client.models.organisation.counters import CountedEntity, EntityCounter


def test_import_id_generation(test_db: Session):
    rows = test_db.query(EntityCounter).count()
    assert rows > 0

    row: EntityCounter = (
        test_db.query(EntityCounter).filter(EntityCounter.prefix == "CCLW").one()
    )
    assert row is not None

    assert row.prefix == "CCLW"
    assert row.counter == 0

    import_id = row.create_import_id(CountedEntity.Family)
    assert import_id == "CCLW.family.i00000001.n0000"
    test_db.flush()

    row: EntityCounter = (
        test_db.query(EntityCounter).filter(EntityCounter.prefix == "CCLW").one()
    )
    assert row.counter == 1
