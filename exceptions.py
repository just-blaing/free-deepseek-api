class DeepSeekError(Exception):
    """Базовое исключение для всех ошибок пакета."""


class NotAuthenticatedError(DeepSeekError):
    """Не найден файл сессии (auth.json) и требуется авторизация."""


class ChatNotFoundError(DeepSeekError):
    """Чат с указанным названием не найден в боковой панели."""


class ResponseNotFoundError(DeepSeekError):
    """Не удалось найти ответ модели в DOM после отправки сообщения."""
