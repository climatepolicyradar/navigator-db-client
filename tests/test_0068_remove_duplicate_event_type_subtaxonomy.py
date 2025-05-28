from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from db_client.models.organisation.corpus import CorpusType
from db_client.utils import get_library_path


def test_remove_duplicate_event_type_subtaxonomy_for_intl_agreements_and_laws_and_policies(
    test_db: Session,
):
    intl_agreements_taxonomy = (
        test_db.query(CorpusType).filter(CorpusType.name == "Intl. agreements").one()
    )

    assert intl_agreements_taxonomy is not None
    assert intl_agreements_taxonomy.valid_metadata["_event"]["event_type"] is not None
    assert intl_agreements_taxonomy.valid_metadata.get("event_type") is None

    laws_and_policies_taxonomy = (
        test_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    assert laws_and_policies_taxonomy is not None
    assert laws_and_policies_taxonomy.valid_metadata["_event"]["event_type"] is not None
    assert laws_and_policies_taxonomy.valid_metadata.get("event_type") is None


def test_restore_event_type_subtaxonomy_for_intl_agreements_and_laws_and_policies(
    test_db: Session,
):
    # Get the engine from test_db
    engine = test_db.get_bind()

    # Configure alembic
    script_directory = get_library_path()
    alembic_ini_path = f"{script_directory}/alembic.ini"
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", f"{script_directory}/alembic")

    # Run downgrade using the test_db connection
    with engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.downgrade(alembic_cfg, "0067")

    # Now check the event_type fields
    intl_agreements_taxonomy = (
        test_db.query(CorpusType).filter(CorpusType.name == "Intl. agreements").one()
    )
    assert intl_agreements_taxonomy is not None
    assert intl_agreements_taxonomy.valid_metadata["_event"]["event_type"] is not None
    assert intl_agreements_taxonomy.valid_metadata["event_type"] is not None
    assert (
        intl_agreements_taxonomy.valid_metadata.get("event_type")
        == intl_agreements_taxonomy.valid_metadata["_event"]["event_type"]
    )

    laws_and_policies_taxonomy = (
        test_db.query(CorpusType).filter(CorpusType.name == "Laws and Policies").one()
    )
    assert laws_and_policies_taxonomy is not None
    assert laws_and_policies_taxonomy.valid_metadata["_event"]["event_type"] is not None
    assert laws_and_policies_taxonomy.valid_metadata["event_type"] is not None
    assert (
        laws_and_policies_taxonomy.valid_metadata["event_type"]
        == laws_and_policies_taxonomy.valid_metadata["_event"]["event_type"]
    )
