from sqlalchemy.orm import Session

from db_client.models.dfce.geography import Geography


def test_geography_subdivisions_exists_with_parent(test_db: Session):
    australia = test_db.query(Geography).filter(Geography.value == "AUS").first()
    assert australia is not None

    new_south_wales = (
        test_db.query(Geography).filter(Geography.value == "AU-NSW").first()
    )
    assert new_south_wales is not None
    assert new_south_wales.display_value == "New South Wales"
    assert new_south_wales.type == "ISO-3166-2"
    assert new_south_wales.parent_id == australia.id

    # Verify no duplicates were created
    assert test_db.query(Geography).filter(Geography.value == "AU-NSW").count() == 1


def test_geography_subdivisions_does_not_exist_without_parent(test_db: Session):
    # These are the countries we know we don't have
    # No parent found for Bonaire, BQ-BO, BES
    # No parent found for Saba, BQ-SA, BES
    # No parent found for Sint Eustatius, BQ-SE, BES
    # No parent found for Avannaata Kommunia, GL-AV, GRL
    # No parent found for Kommune Kujalleq, GL-KU, GRL
    # No parent found for Qeqqata Kommunia, GL-QE, GRL
    # No parent found for Kommune Qeqertalik, GL-QT, GRL
    # No parent found for Kommuneqarfik Sermersooq, GL-SM, GRL
    # No parent found for Ascension, SH-AC, SHN
    # No parent found for Saint Helena, SH-HL, SHN
    # No parent found for Tristan da Cunha, SH-TA, SHN
    # No parent found for Johnston Atoll, UM-67, UMI
    # No parent found for Midway Islands, UM-71, UMI
    # No parent found for Navassa Island, UM-76, UMI
    # No parent found for Wake Island, UM-79, UMI
    # No parent found for Baker Island, UM-81, UMI
    # No parent found for Howland Island, UM-84, UMI
    # No parent found for Jarvis Island, UM-86, UMI
    # No parent found for Kingman Reef, UM-89, UMI
    # No parent found for Palmyra Atoll, UM-95, UMI
    # No parent found for Alo, WF-AL, WLF
    # No parent found for Sigave, WF-SG, WLF
    # No parent found for Uvea, WF-UV, WLF
    assert test_db.query(Geography).filter(Geography.value == "BQ-BO").count() == 0
    assert test_db.query(Geography).filter(Geography.value == "BQ-BO").count() == 0
    assert test_db.query(Geography).filter(Geography.value == "GL-KU").count() == 0
    assert test_db.query(Geography).filter(Geography.value == "UM-81").count() == 0
    assert test_db.query(Geography).filter(Geography.value == "WF-AL").count() == 0
