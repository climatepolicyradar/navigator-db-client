"""Use FK as prefix in counter

Revision ID: 0044
Revises: 0043
Create Date: 2024-07-08 18:11:33.721363

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "ck_entity_counter__prefix_allowed_orgs", "entity_counter", type_="unique"
    )


def downgrade():
    pass  # No way back
