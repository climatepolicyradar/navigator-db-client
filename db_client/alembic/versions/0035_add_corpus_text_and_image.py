"""add corpus text and image

Revision ID: 0035
Revises: 0034
Create Date: 2024-04-30 11:22:43.893840

"""

from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from db_client.models import ORGANISATION_CCLW, ORGANISATION_UNFCCC

# revision identifiers, used by Alembic.
revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


Base = automap_base()


CCLW_TEXT = """
        <p>
          The summary of this document was written by researchers at the <a href="http://lse.ac.uk/grantham" target="_blank"> Grantham Research Institute </a> . 
          If you want to use this summary, please check <a href="https://www.lse.ac.uk/granthaminstitute/cclw-terms-and-conditions" target="_blank"> terms of use </a> for citation and licensing of third party data.
        </p>
"""

UNFCCC_TEXT = """
        <p>
          This document was downloaded from the <a href="https://unfccc.int/" target="_blank"> UNFCCC website </a> . 
          Please check <a href="https://unfccc.int/this-site/terms-of-use" target="_blank"> terms of use </a> for citation and licensing of third party data.
        </p>
"""


def add_image_url_and_text(
    session: Session,
    org_name: str,
    corpus_text: str,
    corpus_image_url: Optional[str] = None,
):

    Org = Base.classes.organisation
    Corpus = Base.classes.corpus
    org = session.query(Org).filter(Org.name == org_name).one()
    corpus = session.query(Corpus).filter(Corpus.organisation_id == org.id).one()

    if corpus_image_url is None:
        corpus.corpus_image_url = f"corpora/{corpus.import_id}/logo.png"
    else:
        corpus.corpus_image_url = corpus_image_url

    corpus.corpus_text = corpus_text
    session.add(corpus)
    session.commit()


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("corpus", sa.Column("corpus_text", sa.Text(), nullable=True))
    op.add_column("corpus", sa.Column("corpus_image_url", sa.Text(), nullable=True))
    # ### end Alembic commands ###

    # Initialise for data migraion

    bind = op.get_bind()
    Base.prepare(autoload_with=bind)

    session = Session(bind=bind)

    # Add new data for CCLW
    add_image_url_and_text(session, ORGANISATION_CCLW, CCLW_TEXT)

    # Add new data for UNFCCC, no image
    add_image_url_and_text(session, ORGANISATION_UNFCCC, UNFCCC_TEXT, "")


def downgrade():
    pass  # no way back