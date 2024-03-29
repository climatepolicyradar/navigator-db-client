from typing import Callable

from sqlalchemy.orm import Session

from db_client.data_migrations.taxonomy_cclw import get_cclw_taxonomy
from db_client.data_migrations.taxonomy_unf3c import get_unf3c_taxonomy
from db_client.data_migrations.utils import has_rows
from db_client.models.dfce.metadata import MetadataOrganisation, MetadataTaxonomy
from db_client.models.organisation.counters import (
    ORGANISATION_CCLW,
    ORGANISATION_UNFCCC,
)
from db_client.models.organisation.users import Organisation


def populate_org_taxonomy(
    db: Session,
    org_name: str,
    org_type: str,
    description: str,
    fn_get_taxonomy: Callable,
) -> None:
    """Populates the taxonomy from the data."""

    # First the org
    org = db.query(Organisation).filter(Organisation.name == org_name).one_or_none()
    if org is None:
        org = Organisation(
            name=org_name, description=description, organisation_type=org_type
        )
        db.add(org)
        db.flush()
        db.commit()

    metadata_org = (
        db.query(MetadataOrganisation)
        .filter(MetadataOrganisation.organisation_id == org.id)
        .one_or_none()
    )
    if metadata_org is None:
        # Now add the taxonomy
        tax = MetadataTaxonomy(
            description=f"{org_name} loaded values",
            valid_metadata=fn_get_taxonomy(),
        )
        db.add(tax)
        db.flush()
        # Finally the link between the org and the taxonomy.
        db.add(
            MetadataOrganisation(
                taxonomy_id=tax.id,
                organisation_id=org.id,
            )
        )
        db.flush()
        db.commit()


def populate_taxonomy(db: Session) -> None:
    if has_rows(db, Organisation):
        return

    populate_org_taxonomy(
        db,
        org_name=ORGANISATION_CCLW,
        org_type="Academic",
        description="Climate Change Laws of the World",
        fn_get_taxonomy=get_cclw_taxonomy,
    )
    populate_org_taxonomy(
        db,
        org_name=ORGANISATION_UNFCCC,
        org_type="UN",
        description="United Nations Framework Convention on Climate Change",
        fn_get_taxonomy=get_unf3c_taxonomy,
    )
