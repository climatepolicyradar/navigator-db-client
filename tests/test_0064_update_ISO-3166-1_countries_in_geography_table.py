from sqlalchemy.orm import Session

from db_client.models.dfce.geography import Geography


def test_geography_updates_and_add_vat(test_db: Session):
    # updates to the new ISO values
    tur = test_db.query(Geography).filter(Geography.value == "TUR").first()
    assert tur is not None
    assert tur.display_value == "Türkiye"

    # adds missing countries
    vat = test_db.query(Geography).filter(Geography.value == "VAT").first()
    assert vat is not None
    assert vat.display_value == "Holy See (Vatican City State)"
