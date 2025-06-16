import uuid
import secrets
import random
import string
from tests.test_backend.data.endpoints.Board.constants import (
    MAX_BOARD_NAME_LENGTH,
    BOARD_CUSTOM_FIELD_MAX_DESCRIPTION_LENGTH,
    BOARD_CUSTOM_FIELD_MAX_TITLE_LENGTH,
)


def generate_space_name() -> str:
    """
    Генерирует уникальное имя для Space.
    Пример: space_1a2b3c
    """
    return f'space_{uuid.uuid4().hex[:12]}'


def generate_project_name() -> str:
    """
    Генерирует уникальное имя для Project.
    Пример: project_abc123
    """
    return f'project_{uuid.uuid4().hex[:12]}'


def generate_slug(min_len: int = 4, max_len: int = 8) -> str:
    """
    Генерирует случайный slug из латинских букв.
    Пример: AbCdEf
    """
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_letters, k=length))


def generate_board_name(min_len: int = 1, max_len=MAX_BOARD_NAME_LENGTH):
    """
    Генерирует уникальное имя для Project.
    Пример: project_abc123
    """
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_letters, k=length))


def generate_custom_field_title(min_len: int = 1, max_len=BOARD_CUSTOM_FIELD_MAX_TITLE_LENGTH) -> str:
    """
    Генерирует строку указанной длины, состоящую из латинских букв и цифр.
    Используется для поля title в кастомных полях борды.

    :param length: Длина генерируемого заголовка.
    :return: Случайная строка.
    """
    chars = string.ascii_letters + string.digits
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(chars, k=length))


def generate_custom_field_description(min_len: int = 1, max_len=BOARD_CUSTOM_FIELD_MAX_DESCRIPTION_LENGTH) -> str:
    """Генерирует описание кастомного поля максимальной длины (по умолчанию)."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))


def generate_object_id() -> str:
    return secrets.token_hex(12)
