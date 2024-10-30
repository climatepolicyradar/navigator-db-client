"""Add _event sub taxonomy.

Revision ID: 0057
Revises: 0056
Create Date: 2024-10-29 14:01:33.721363

"""

import os

import sqlalchemy as sa
from alembic import op

from db_client.utils import get_library_path

revision = "0057"
down_revision = "0056"
branch_labels = None
depends_on = None


def upgrade():
    # Get the path to the SQL file
    sql_file_path = os.path.join(
        get_library_path(),
        "alembic",
        "versions",
        "data",
        "0057",
        "add-_event-schema.sql",
    )

    # Read the SQL file
    with open(sql_file_path, "r") as file:
        sql_commands = file.read()

    # Execute the SQL commands
    op.execute(sa.text(sql_commands))


def downgrade():
    pass  # No way back
