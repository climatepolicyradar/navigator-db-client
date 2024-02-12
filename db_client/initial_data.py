#!/usr/bin/env python3

import os
from typing import Optional

from sqlalchemy.exc import IntegrityError

from db_client.models.app import AppUser

from db_client.data_migrations import (
    populate_counters,
    populate_document_type,
    populate_document_role,
    populate_document_variant,
    populate_event_type,
    populate_geo_statistics,
    populate_geography,
    populate_language,
    populate_taxonomy,
)


def run_data_migrations(db):
    """Populate lookup tables with standard values"""
    populate_document_type(db)
    populate_document_role(db)
    populate_document_variant(db)
    populate_event_type(db)
    populate_geography(db)
    populate_language(db)
    populate_taxonomy(db)
    populate_counters(db)

    db.flush()  # Geography data is used by geo-stats so flush

    populate_geo_statistics(db)
    # TODO - framework, keyword, instrument, hazard


def create_user(db, name, email, password, get_password_hash):
    with db.begin_nested():
        db_user = AppUser(
            email=email,
            name=name,
            hashed_password=get_password_hash(password),
            is_superuser=True,
        )
        db.add(db_user)
        db.flush


def create_superuser(db, get_password_hash) -> None:
    superuser_email = os.getenv("SUPERUSER_EMAIL")
    try:
        create_user(
            db, "CPR Super User", superuser_email, os.getenv("SUPERUSER_PASSWORD"), get_password_hash
        )
    except IntegrityError:
        print(
            f"Skipping - superuser already exists with email/username {superuser_email}"
        )


def populate_initial_data(db, get_password_hash):
    if get_password_hash:
        print("Creating superuser...")
        create_superuser(db, get_password_hash)

    print("Running data migrations...")
    run_data_migrations(db)

