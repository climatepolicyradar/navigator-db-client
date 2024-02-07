from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine


def run_migrations(alembic_files_location: str, engine: Engine) -> None:
    """
    Apply alembic migrations.

    Call through subprocess as opposed to the alembic command function as the server
    startup never completed when using the alembic solution.
    """
    # Path to alembic.ini
    alembic_ini_path = f"{alembic_files_location}/alembic.ini"
    alembic_cfg = Config(alembic_ini_path)

    # Set the script location
    alembic_cfg.set_main_option("script_location", f"{alembic_files_location}/alembic")

    # Run the migration
    with engine.begin() as connection:
            alembic_cfg.attributes['connection'] = connection
            command.upgrade(alembic_cfg, "head")
