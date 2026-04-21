import contextvars

# Context variable to store the current user_id for the request
user_id_ctx = contextvars.ContextVar("user_id", default=None)

def set_current_user_id(user_id: str):
    user_id_ctx.set(user_id)

def get_current_user_id() -> str | None:
    return user_id_ctx.get()
