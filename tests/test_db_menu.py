import sys
import types
from unittest import mock

# Provide stub mysql modules so DatabaseCore can import without the real package
fake_mysql = types.ModuleType("mysql")
fake_mysql.connector = types.ModuleType("mysql.connector")
fake_mysql.connector.Error = Exception
fake_mysql.connector.errorcode = types.SimpleNamespace()
fake_mysql.connector.connect = mock.Mock()
pooling = types.ModuleType("mysql.connector.pooling")
pooling.MySQLConnectionPool = mock.Mock()
sys.modules.setdefault("mysql", fake_mysql)
sys.modules.setdefault("mysql.connector", fake_mysql.connector)
sys.modules.setdefault("mysql.connector.pooling", pooling)


def test_db_menu_provides_test_connection_option_and_uses_engine():
    from database import db_menu as db_menu_mod

    fake_engine = mock.Mock()
    fake_core = mock.Mock()

    with mock.patch.object(db_menu_mod, "DbEngine", return_value=fake_engine) as eng_cls, \
         mock.patch.object(db_menu_mod, "DatabaseCore") as core_cls, \
         mock.patch.object(db_menu_mod.menu_utils, "show_menu") as show_menu:
        core_cls.from_config.return_value = fake_core

        def fake_show_menu(title, options, exit_label):
            # Menu contains only the test connection option
            assert options["1"][0].lower().startswith("test")
            # Simulate selecting the option
            options["1"][1]()

        show_menu.side_effect = fake_show_menu

        db_menu_mod.db_menu()

        core_cls.from_config.assert_called_once()
        eng_cls.assert_called_once_with(fake_core)
        fake_engine.init.assert_called_once()
        fake_engine.is_ready.assert_called_once()
        fake_engine.shutdown.assert_called_once()


def test_action_database_menu_invokes_db_menu():
    import main

    with mock.patch.object(main, "db_menu") as menu:
        main.action_database_menu()
        menu.assert_called_once()
