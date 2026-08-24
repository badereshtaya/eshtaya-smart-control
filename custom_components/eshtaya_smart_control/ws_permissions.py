"""WebSocket permission adapters for Eshtaya Smart Control v2.1."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .access_control import require_permission


def permissioned_admin_command(command: Callable[..., Any], permission: str) -> Callable[..., Any]:
    """Replace the outer Home Assistant admin guard with an Eshtaya permission guard.

    Existing v2 command handlers use ``@websocket_api.require_admin`` as their
    outermost decorator. Home Assistant decorators preserve ``__wrapped__``, so
    unwrapping exactly one layer keeps the command schema/async-response wrapper
    while replacing only the admin requirement. Home Assistant administrators
    still receive every Eshtaya permission through AccessControlManager.
    """
    inner = getattr(command, "__wrapped__", command)
    return require_permission(permission)(inner)
