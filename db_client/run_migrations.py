import os
import subprocess
from alembic import context


def run_migrations(alembic_files_location: str) -> None:
    """
    Apply alembic migrations.

    Call through subprocess as opposed to the alembic command function as the server
    startup never completed when using the alembic solution.
    """
    # Path to alembic.ini
    alembic_ini_path = f"{alembic_files_location}/alembic.ini"

    # Set the script location
    config = context.config
    config.set_main_option('script_location', f"{alembic_files_location}/alembic")

    subprocess.run(["alembic", "-c", alembic_ini_path, "upgrade", "head"], check=True)
