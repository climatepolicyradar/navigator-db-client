"""Add the CCLW Corpus and Corpus Type (old taxonomy)

Revision ID: 0031
Revises: 0030
Create Date: 2024-03-21 sometime after breakfast

"""

from alembic import op
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.data_migrations.taxonomy_cclw import get_cclw_taxonomy

# revision identifiers, used by Alembic.
revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None

Base = automap_base()


def get_cclw(session, Org):
    return session.query(Org).filter(Org.name == "CCLW").one()


def add_corpus_type(session, CorpusType, name, description, valid_metadata):
    corpus_type = CorpusType(
        name=name,
        description=description,
        valid_metadata=valid_metadata,
    )
    session.add(corpus_type)
    session.flush()
    return corpus_type


def add_corpus(session, Corpus, title, description, org, corpus_type):
    # NOTE: we cannot use create_import_id here.. so pinch the code
    n = 0  # The fourth quad is historical
    i_value = str(1).zfill(8)
    n_value = str(n).zfill(4)
    import_id = f"{org.name}.corpus.i{i_value}.n{n_value}"
    corpus = Corpus(
        import_id=import_id,
        title=title,
        description=description,
        organisation_id=org.id,
        corpus_type=corpus_type,
    )
    session.add(corpus)
    session.flush()
    return corpus


def link_families_to_corpus(session, families, corpus):
    session.begin(subtransactions=True)

    for family in families:
        # insert into FamilyCorpus
        family.corpus_collection.append(corpus)
    session.commit()


def upgrade():
    bind = op.get_bind()
    session: Session = Session(bind=bind)

    Base.prepare(autoload_with=bind)
    Org = Base.classes.organisation
    Corpus = Base.classes.corpus
    CorpusType = Base.classes.corpus_type

    # Create Corpus Types
    law_and_policy = add_corpus_type(
        session,
        CorpusType,
        "Laws and Policies",
        "Laws and policies",
        get_cclw_taxonomy(),
    )

    # Create Corpus
    cclw = get_cclw(session, Org)
    # Change the name
    cclw.name = "LSE CCLW team"
    corpus = add_corpus(
        session,
        Corpus,
        "CCLW national policies",
        "CCLW national policies",
        cclw,
        law_and_policy,
    )
    session.commit()

    # Link all families to their respective corpus
    link_families_to_corpus(session, cclw.family_collection, corpus)


def downgrade():
    # There is no way back
    pass
