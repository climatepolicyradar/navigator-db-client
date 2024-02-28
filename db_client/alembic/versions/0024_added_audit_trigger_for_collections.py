"""
Added audit trigger for collections

Revision ID: 0024
Revises: 0023
Create Date: 2023-11-22 22:36:26.134026

"""
import sqlalchemy as sa
from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger

from alembic import op

# revision identifiers, used by Alembic.
revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "collection",
        sa.Column(
            "created",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "collection",
        sa.Column(
            "last_modified",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    public_update_2_collection_last_modified = PGFunction(
        schema="public",
        signature="update_2_collection_last_modified()",
        definition="""
    RETURNS TRIGGER AS $$
    BEGIN
        if tg_op = 'DELETE' then
            UPDATE collection
            SET last_modified = NOW()
            WHERE import_id = OLD.collection_import_id;
        else
            UPDATE collection
            SET last_modified = NOW()
            WHERE import_id = NEW.collection_import_id;
        end if;
        RETURN NEW;
    END;
    $$ language 'plpgsql'""",
    )
    op.create_entity(public_update_2_collection_last_modified)  # type: ignore

    public_collection_update_collection_last_modified = PGTrigger(
        schema="public",
        signature="update_collection_last_modified",
        on_entity="public.collection",
        is_constraint=False,
        definition="""
    BEFORE UPDATE ON public.collection
    FOR EACH ROW
    EXECUTE PROCEDURE public.update_1_last_modified()""",
    )
    op.create_entity(public_collection_update_collection_last_modified)  # type: ignore

    public_collection_family_update_collection_last_modified = PGTrigger(
        schema="public",
        signature="update_collection_last_modified",
        on_entity="public.collection_family",
        is_constraint=False,
        definition="""
    BEFORE INSERT OR UPDATE OR DELETE ON public.collection_family
    FOR EACH ROW
    EXECUTE PROCEDURE public.update_2_collection_last_modified()""",
    )
    op.create_entity(public_collection_family_update_collection_last_modified)  # type: ignore

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    public_collection_family_update_collection_last_modified = PGTrigger(
        schema="public",
        signature="update_collection_last_modified",
        on_entity="public.collection_family",
        is_constraint=False,
        definition="""
    BEFORE INSERT OR UPDATE OR DELETE ON public.collection_family
    FOR EACH ROW
    EXECUTE PROCEDURE public.update_2_collection_last_modified()""",
    )
    op.drop_entity(public_collection_family_update_collection_last_modified)  # type: ignore

    public_collection_update_collection_last_modified = PGTrigger(
        schema="public",
        signature="update_collection_last_modified",
        on_entity="public.collection",
        is_constraint=False,
        definition="""
    BEFORE UPDATE ON public.collection
    FOR EACH ROW
    EXECUTE PROCEDURE public.update_1_last_modified()""",
    )
    op.drop_entity(public_collection_update_collection_last_modified)  # type: ignore

    public_update_2_collection_last_modified = PGFunction(
        schema="public",
        signature="update_2_collection_last_modified()",
        definition="""
    RETURNS TRIGGER AS $$
    BEGIN
        if tg_op = 'DELETE' then
            UPDATE collection
            SET last_modified = NOW()
            WHERE import_id = OLD.collection_import_id;
        else
            UPDATE collection
            SET last_modified = NOW()
            WHERE import_id = NEW.collection_import_id;
        end if;
        RETURN NEW;
    END;
    $$ language 'plpgsql'""",
    )
    op.drop_entity(public_update_2_collection_last_modified)  # type: ignore

    op.drop_column("collection", "last_modified")
    op.drop_column("collection", "created")
    # ### end Alembic commands ###
