from pytest_alembic.tests import (
    test_model_definitions_match_ddl,
    test_single_head_revision,
    # test_up_down_consistency, TODO: Review and fix the dowgrade migrations
    test_upgrade,
)