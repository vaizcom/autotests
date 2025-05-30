import uuid
import random
import string
from backend_tests.data.endpoints.Board.constants import MAX_BOARD_NAME_LENGTH

def generate_space_name() -> str:
    """
    Генерирует уникальное имя для Space.
    Пример: space_1a2b3c
    """
    return f"space_{uuid.uuid4().hex[:12]}"


def generate_project_name() -> str:
    """
    Генерирует уникальное имя для Project.
    Пример: project_abc123
    """
    return f"project_{uuid.uuid4().hex[:12]}"


def generate_board_name() -> str:
    """
    Генерирует уникальное имя для Board.
    Пример: board_a1b2c3
    """
    return f"board_{uuid.uuid4().hex[:12]}"


def generate_slug(min_len: int = 4, max_len: int = 8) -> str:
    """
    Генерирует случайный slug из латинских букв.
    Пример: AbCdEf
    """
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_letters, k=length))

def generate_board_name(min_len: int = 1, max_len = MAX_BOARD_NAME_LENGTH):
    """
    Генерирует уникальное имя для Project.
    Пример: project_abc123
    """
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_letters, k=length))