from db_client import run_migrations  # Adjust the import path as necessary


def test_run_migrations_with_pytest_mocker(mocker):
    # Mocks
    test_path = "/test_path/test_subpath"
    mock_realpath = mocker.patch(
        "db_client.run_migrations_script.os.path.realpath",
        return_value=test_path + "test.py",
    )
    mock_dirname = mocker.patch(
        "db_client.run_migrations_script.os.path.dirname", return_value=test_path
    )
    mock_Config = mocker.patch("db_client.run_migrations_script.Config")
    mock_upgrade = mocker.patch("db_client.run_migrations_script.command.upgrade")

    mock_engine = mocker.MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_engine

    # Run
    run_migrations(mock_engine)

    # Asserts
    mock_realpath.assert_called_once()
    mock_dirname.assert_called_once()
    mock_Config.assert_called_once_with(test_path + "/alembic.ini")
    mock_Config().set_main_option.assert_called_once_with(
        "script_location", test_path + "/alembic"
    )
    mock_upgrade.assert_called_once()
    mock_upgrade.assert_called_with(mock_Config(), "head")
