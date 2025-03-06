"""Add reports which is a new corpus type to the family category model

Revision ID: 0059
Revises: 0058
Create Date: 2025-02-27 11:56:49.987901

"""

from alembic import op
from sqlalchemy import MetaData, String

from db_client.models.dfce.concept import Concept, FamilyConcept

# revision identifiers, used by Alembic.
revision = "0059"
down_revision = "0058"
branch_labels = None
depends_on = None


def upgrade():
    # Get the database connection from Alembic's context
    bind = op.get_bind()

    metadata = MetaData()
    metadata.reflect(bind=bind)

    if "concept" not in metadata.tables:
        Concept.__table__.create(bind)

    if "family_concept" not in metadata.tables:
        FamilyConcept.__table__.create(bind)
    else:
        # Make the relation column nullable
        op.alter_column(
            "family_concept", "relation", existing_type=String(), nullable=True
        )


def downgrade():
    bind = op.get_bind()
    metadata = MetaData()
    metadata.reflect(bind=bind)

    if "family_concept" in metadata.tables:
        # Make the relation column non-nullable again
        op.alter_column(
            "family_concept", "relation", existing_type=String(), nullable=False
        )
        metadata.tables["family_concept"].drop(bind)

    if "concept" in metadata.tables:
        metadata.tables["concept"].drop(bind)
