import re

HRID_PATTERN = r"^[A-Z]+-\d+$"

def validate_hrid(task_hrid: str):
    """Проверяет, что hrid соответствует формату <префикс>-<число>."""
    assert re.match(HRID_PATTERN, task_hrid), f"Поле 'hrid' имеет некорректный формат: {task_hrid}"