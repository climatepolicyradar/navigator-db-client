import sqlalchemy as sa
from sqlalchemy import PrimaryKeyConstraint

from db_client.models.base import Base
from db_client.models.organisation.organisation import Organisation


class AppUser(Base):
    """Table of app users in the system."""

    __tablename__ = "app_user"

    email = sa.Column(sa.String, primary_key=True, nullable=False)
    name = sa.Column(sa.String)
    hashed_password = sa.Column(sa.String)
    is_superuser = sa.Column(sa.Boolean, default=False, nullable=False)


class OrganisationUser(Base):
    """Link table for admin and organisation."""

    __tablename__ = "organisation_admin"

    appuser_email = sa.Column(sa.String, sa.ForeignKey(AppUser.email), nullable=False)
    organisation_id = sa.Column(sa.ForeignKey(Organisation.id), nullable=False)
    job_title = sa.Column(sa.String)
    is_active = sa.Column(sa.Boolean, default=False, nullable=False)
    is_admin = sa.Column(sa.Boolean, default=False, nullable=False)

    PrimaryKeyConstraint(appuser_email, organisation_id)
