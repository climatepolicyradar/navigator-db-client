import pytest
from sqlalchemy.orm import Session

from db_client.models.dfce.geography import Geography


@pytest.mark.parametrize(
    "iso_value,expected_display_value",
    [("TUR", "Türkiye"), ("VAT", "Holy See (Vatican City State)")],
)
def test_geography_updates_and_add_vat(
    test_db: Session, iso_value: str, expected_display_value: str
):
    geography = test_db.query(Geography).filter(Geography.value == iso_value).first()
    assert geography is not None
    assert geography.display_value == expected_display_value


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


# These are the countries we know we don't have
@pytest.mark.parametrize(
    "iso_value",
    [
        "BQ-BO",  # No parent found for Bonaire, BQ-BO, BES
        "BQ-SA",  # No parent found for Saba, BQ-SA, BES
        "BQ-SE",  # No parent found for Sint Eustatius, BQ-SE, BES
        "GL-AV",  # No parent found for Avannaata Kommunia, GL-AV, GRL
        "GL-KU",  # No parent found for Kommune Kujalleq, GL-KU, GRL
        "GL-QE",  # No parent found for Qeqqata Kommunia, GL-QE, GRL
        "GL-QT",  # No parent found for Kommune Qeqertalik, GL-QT, GRL
        "GL-SM",  # No parent found for Kommuneqarfik Sermersooq, GL-SM, GRL
        "SH-AC",  # No parent found for Ascension, SH-AC, SHN
        "SH-HL",  # No parent found for Saint Helena, SH-HL, SHN
        "SH-TA",  # No parent found for Tristan da Cunha, SH-TA, SHN
        "UM-67",  # No parent found for Johnston Atoll, UM-67, UMI
        "UM-71",  # No parent found for Midway Islands, UM-71, UMI
        "UM-76",  # No parent found for Navassa Island, UM-76, UMI
        "UM-79",  # No parent found for Wake Island, UM-79, UMI
        "UM-81",  # No parent found for Baker Island, UM-81, UMI
        "UM-84",  # No parent found for Howland Island, UM-84, UMI
        "UM-86",  # No parent found for Jarvis Island, UM-86, UMI
        "UM-89",  # No parent found for Kingman Reef, UM-89, UMI
        "UM-95",  # No parent found for Palmyra Atoll, UM-95, UMI
        "WF-AL",  # No parent found for Alo, WF-AL, WLF
        "WF-SG",  # No parent found for Sigave, WF-SG, WLF
        "WF-UV",  # No parent found for Uvea, WF-UV, WLF
    ],
)
def test_geography_subdivisions_does_not_exist_without_parent(
    test_db: Session, iso_value: str
):
    assert test_db.query(Geography).filter(Geography.value == iso_value).count() == 0
