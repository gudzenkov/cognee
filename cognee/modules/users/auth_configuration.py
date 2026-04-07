import os


def _parse_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() == "true"


def require_authentication_enabled() -> bool:
    return _parse_bool_env("REQUIRE_AUTHENTICATION", default=False)


def backend_access_control_env_value() -> bool | None:
    value = os.getenv("ENABLE_BACKEND_ACCESS_CONTROL")
    if value is None:
        return None

    return value.strip().lower() == "true"
