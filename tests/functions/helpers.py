"""
Helpers - Functions not included in the DFCE functions

This is necessary to help setup the tests without the need for running the
migrations. Where possible it uses the DFCE functions, however for creating
the CorpusType for example which is normally done with a migration, this is
captured in these functions below.
"""

from db_client.functions.dfce_helpers import add_families, add_organisation
from db_client.models.dfce.family import Family
from db_client.models.dfce.geography import Geography
from db_client.models.organisation import Corpus, CorpusType


def metadata_build(db, taxonomy):
    """Fixture for tests relating to metadata.

    :param _type_ db: The postgres db fixture.
    :yield _type_: A database populated with the test metadata data.
    """

    # First add the dummy Organisation to the database
    dummy_org = add_organisation(db, "Org1", "", "")

    # now add a dummy CorpusType with the taxonomy passed in
    # NOTE: this is normally done with a data migration
    dummy_corpus_type = CorpusType(
        name="Dummy CorpusType", description="", valid_metadata=taxonomy
    )
    db.add(dummy_corpus_type)
    db.commit()

    # now add a dummy Corpus to the Organisation with the new CorpusType
    # NOTE: this is normally done with a data migration
    dummy_corpus = Corpus(
        import_id="Org1.Corpus.1.1",
        title="Dummy Corpus",
        description="",
        corpus_type_name=dummy_corpus_type.name,
        organisation_id=dummy_org.id,
    )
    db.add(dummy_corpus)
    db.commit()

    return dummy_org, dummy_corpus, dummy_corpus_type


def family_build(db, org, corpus, metadata) -> Family:

    db.add(Geography(id=1, display_value="nowhere", slug="s"))
    db.commit()

    family = {
        "import_id": f"{org.name}.family.1.1",
        "corpus_import_id": corpus.import_id,
        "title": "family",
        "slug": "slug",
        "description": "Summary",
        "geography_id": 1,
        "category": "Executive",
        "documents": [],
        "metadata": metadata,
    }
    add_families(db, families=[family], org_id=org.id)
    return db.query(Family).filter(Family.import_id == family["import_id"]).one()
