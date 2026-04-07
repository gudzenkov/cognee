import importlib
import os
import sys
from unittest.mock import patch

MODULE_NAME = "cognee.modules.users.auth_configuration"


def import_auth_configuration():
    if MODULE_NAME in sys.modules:
        del sys.modules[MODULE_NAME]

    return importlib.import_module(MODULE_NAME)


class TestAuthConfigurationDefaults:
    def test_require_authentication_defaults_to_false(self):
        with patch.dict(os.environ, {}, clear=True):
            auth_configuration = import_auth_configuration()
            assert not auth_configuration.require_authentication_enabled()

    def test_backend_access_control_defaults_to_none(self):
        with patch.dict(os.environ, {}, clear=True):
            auth_configuration = import_auth_configuration()
            assert auth_configuration.backend_access_control_env_value() is None


class TestAuthConfigurationParsing:
    def test_backend_access_control_env_parses_false(self):
        with patch.dict(
            os.environ,
            {
                "ENABLE_BACKEND_ACCESS_CONTROL": "false",
            },
            clear=True,
        ):
            auth_configuration = import_auth_configuration()
            assert auth_configuration.backend_access_control_env_value() is False

    def test_backend_access_control_env_parses_true(self):
        with patch.dict(
            os.environ,
            {
                "ENABLE_BACKEND_ACCESS_CONTROL": "true",
            },
            clear=True,
        ):
            auth_configuration = import_auth_configuration()
            assert auth_configuration.backend_access_control_env_value() is True
