from typing import List, Tuple

from sqlalchemy.orm import Session

from db_client.models.dfce import (
    Collection,
    CollectionFamily,
    CollectionOrganisation,
    Family,
    FamilyDocument,
    FamilyEvent,
    FamilyGeography,
    FamilyMetadata,
    Slug,
)
from db_client.models.dfce.family import FamilyCorpus
from db_client.models.document.physical_document import (
    Language,
    PhysicalDocument,
    PhysicalDocumentLanguage,
)
from db_client.models.organisation.organisation import Organisation


def add_organisation(
    db: Session, name: str, description: str, type: str, display_name: str
) -> Organisation:
    org = Organisation(
        name=name,
        description=description,
        organisation_type=type,
        display_name=display_name,
    )
    db.add(org)
    db.commit()
    return org


def add_collections(db: Session, collections, org_id=1):
    for c in collections:
        db.add(
            Collection(
                import_id=c["import_id"],
                title=c["title"],
                description=c["description"],
                valid_metadata=c["metadata"],
            )
        )
    db.flush()
    for c in collections:
        db.add(
            CollectionOrganisation(
                collection_import_id=c["import_id"], organisation_id=org_id
            )
        )
    db.commit()


def add_families(db: Session, families, org_id=1):
    for f in families:
        db.add(
            Family(
                import_id=f["import_id"],
                title=f["title"],
                description=f["description"],
                family_category=f["category"],
            )
        )
        db.flush()

        new_slug = Slug(
            family_import_id=f["import_id"],
            family_document_import_id=None,
            name=f["slug"],
        )
        db.add(new_slug)

        geo_ids = (
            f["geography_id"]
            if isinstance(f["geography_id"], list)
            else [f["geography_id"]]
        )
        for geo_id in geo_ids:
            db.add(
                FamilyGeography(
                    family_import_id=f["import_id"],
                    geography_id=geo_id,
                )
            )

        for d in f["documents"]:
            add_document(db, f["import_id"], d)

        metadata_value = {}
        if "metadata" in f:
            metadata_value = f["metadata"]

        db.add(
            FamilyMetadata(
                family_import_id=f["import_id"],
                value=metadata_value,
            )
        )
        if "corpus_import_id" in f:
            db.add(
                FamilyCorpus(
                    family_import_id=f["import_id"],
                    corpus_import_id=f["corpus_import_id"],
                )
            )

    db.commit()


def add_event(db: Session, family_import_id, family_document_import_id, e):
    """Adds an Event"""

    # Note: should we be checking the "Eventable Type",
    #       e.g. Legislation from family category?

    db.add(
        FamilyEvent(
            family_import_id=family_import_id,
            family_document_import_id=family_document_import_id,
            import_id=e["import_id"],
            title=e["title"],
            date=e["date"],
            event_type_name=e["type"],
            status=e["status"],
            valid_metadata={
                "event_type": [e["type"]],
                "datetime_event_name": [e["valid_metadata"]["datetime_event_name"]],
            },
        )
    )


def add_document(db: Session, family_import_id, d):
    pd = PhysicalDocument(
        title=d["title"],
        md5_sum=d["md5_sum"],
        cdn_object=None,
        source_url=d["url"],
        content_type=d["content_type"],
    )

    db.add(pd)
    db.flush()

    db.add(
        FamilyDocument(
            family_import_id=family_import_id,
            physical_document_id=pd.id,
            import_id=d["import_id"],
            variant_name=d["language_variant"],
            document_status=d["status"],
            valid_metadata=d["metadata"],
        )
    )
    db.flush()

    for lang in d["languages"]:
        db_lang = db.query(Language).filter(Language.language_code == lang).one()
        db.add(
            PhysicalDocumentLanguage(
                language_id=db_lang.id, document_id=pd.id, source="User", visible=True
            )
        )

    new_slug = Slug(
        family_import_id=None,
        family_document_import_id=d["import_id"],
        name=d["slug"],
    )
    db.add(new_slug)

    for e in d["events"]:
        add_event(db, family_import_id, d["import_id"], e)


def link_collection_family(db: Session, links: List[Tuple[str, str]]):
    for collection_import_id, family_import_id in links:
        db.add(
            CollectionFamily(
                collection_import_id=collection_import_id,
                family_import_id=family_import_id,
            )
        )
    db.flush()
