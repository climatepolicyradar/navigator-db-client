import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from db_client.models.base import Base
from db_client.models.organisation.organisation import Organisation


class CorpusType(Base):

    __tablename__ = "corpus_type"

    name = sa.Column(sa.Text, primary_key=True)
    description = sa.Column(sa.Text, nullable=False)
    valid_metadata = sa.Column(postgresql.JSONB, nullable=False)


class Corpus(Base):

    __tablename__ = "corpus"

    import_id = sa.Column(sa.Text, primary_key=True)
    title = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    corpus_text = sa.Column(sa.Text)
    corpus_image_url = sa.Column(sa.Text)
    organisation_id = sa.Column(sa.ForeignKey(Organisation.id), nullable=False)
    corpus_type_name = sa.Column(sa.ForeignKey(CorpusType.name), nullable=False)
