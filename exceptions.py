class DeepSeekError(Exception):
    """базовое исключение для всех ошибок пакета"""


class NotAuthenticatedError(DeepSeekError):
    """не найден файл сессии (auth.json) и требуется авторизация"""


class ChatNotFoundError(DeepSeekError):
    """чат с указанным названием не найден в боковой панели"""


class ResponseNotFoundError(DeepSeekError):
    """не удалось найти ответ модели в DOM после отправки сообщения"""
