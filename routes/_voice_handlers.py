"""
BackPocket OS — Voice Intent Handler Registry
Each handler implements the actual business logic for a voice intent.
Handlers are registered incrementally in chunks 5-14.
"""

import logging

logger = logging.getLogger(__name__)

_HANDLERS: dict[str, callable] = {}


def register_handler(intent: str):
    """Decorator to register an intent handler."""
    def decorator(fn):
        _HANDLERS[intent] = fn
        return fn
    return decorator


async def execute_handler(intent: str, params: dict, screen_context: str, metadata: dict | None = None) -> dict:
    """Execute the registered handler for an intent."""
    handler = _HANDLERS.get(intent)
    if not handler:
        logger.warning(f"No handler for intent: {intent}")
        return {"message": f"Intent '{intent}' not yet implemented."}
    return await handler(params, screen_context, metadata)


def list_handlers() -> list[str]:
    return list(_HANDLERS.keys())

# Import handler modules to automatically register them via the decorator

