"""Add the CCLW Corpus and Corpus Type (old taxonomy)

Revision ID: 0031
Revises: 0030
Create Date: 2024-03-21 sometime after breakfast

"""


from alembic import op
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session 

from data_migrations.taxonomy_cclw import get_cclw_taxonomy

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


def add_corpus(session, Corpus, EntityCounter, title, description, org, corpus_type):
    counter = session.query(EntityCounter).filter(EntityCounter.prefix == org.name).one()
    corpus = Corpus(
        import_id = counter.create_import_id("corpus"),
        title = title,
        description = description,
        organisation_id = org.id,
        corpus_type = corpus_type,
    )
    session.add(corpus)
    session.flush()
    return corpus


def link_families_to_corpus(session, FamilyOrganisation, FamilyCorpus, cclw, corpus):
    families = session.query(FamilyOrganisation).filter(FamilyOrganisation.organisaton_id == cclw.id).all()
    session.begin()
    for family_import_id in [ f.import_id for f in families]:
        # insert into FamilyCorpus
        session.add(FamilyCorpus(
            family_import_id = family_import_id,
            corpus_import_id = corpus.import_id,
        ))
    session.commit()


def upgrade():
    bind = op.get_bind()
    session: Session = Session(bind=bind)

    Base.prepare(autoload_with=bind)
    Org = Base.classes.organisation
    Corpus = Base.classes.corpus
    CorpusType = Base.classes.corpus_type
    EntityCounter = Base.classes.entity_counter
    FamilyOrganisation = Base.classes.family_organisation
    FamilyCorpus = Base.classes.family_corpus

    # Create Corpus Types
    law_and_policy = add_corpus_type(session, CorpusType, "Law & Policy", "Laws and policies", get_cclw_taxonomy())

    # Create Corpus
    cclw = get_cclw(session, Org)
    corpus = add_corpus(session, Corpus, EntityCounter, "", "", cclw, law_and_policy)
    session.commit()

    # Link all families to their respective corpus
    link_families_to_corpus(session, FamilyOrganisation, FamilyCorpus, cclw, corpus)


def downgrade():
    # There is no way back
    pass

