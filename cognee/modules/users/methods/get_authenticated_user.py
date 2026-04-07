import sys
from typing import Optional
from fastapi import Depends, HTTPException
from ..models import User
from ..get_fastapi_users import get_fastapi_users
from .get_default_user import get_default_user
from cognee.shared.logging_utils import get_logger
from cognee.modules.users.auth_configuration import require_authentication_enabled


logger = get_logger("get_authenticated_user")

REQUIRE_AUTHENTICATION = require_authentication_enabled()

fastapi_users = get_fastapi_users()

_auth_dependency = fastapi_users.current_user(active=True, optional=True)


def authentication_required() -> bool:
    client_module = sys.modules.get("cognee.api.client")
    if client_module is not None and hasattr(client_module, "REQUIRE_AUTHENTICATION"):
        return client_module.REQUIRE_AUTHENTICATION

    return require_authentication_enabled()


async def get_authenticated_user(
    user: Optional[User] = Depends(_auth_dependency),
) -> User:
    """
    Get authenticated user with environment-controlled behavior:
    - If REQUIRE_AUTHENTICATION=true: Enforces authentication (raises 401 if not authenticated)
    - If REQUIRE_AUTHENTICATION=false: Falls back to default user if not authenticated

    Always returns a User object for consistent typing.
    """
    if user is None:
        if authentication_required():
            raise HTTPException(status_code=401, detail="Unauthorized")

        # When authentication is optional and user is None, use default user
        try:
            user = await get_default_user()
        except Exception as e:
            # Convert any get_default_user failure into a proper HTTP 500 error
            logger.error(f"Failed to create default user: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create default user: {str(e)}"
            ) from e

    return user
