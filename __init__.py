from .client import DeepSeekClient
from .exceptions import (
    DeepSeekError,
    NotAuthenticatedError,
    ChatNotFoundError,
    ResponseNotFoundError,
)

__version__ = "0.1.0"

__all__ = [
    "DeepSeekClient",
    "DeepSeekError",
    "NotAuthenticatedError",
    "ChatNotFoundError",
    "ResponseNotFoundError",
]
