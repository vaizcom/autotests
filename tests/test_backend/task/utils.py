import re

import allure

from test_backend.data.endpoints.User.profile_endpoint import get_profile_endpoint

HRID_PATTERN = r"^[A-Z]+-\d+$"

def validate_hrid(task_hrid: str):
    """Проверяет, что hrid соответствует формату <префикс>-<число>."""
    assert re.match(HRID_PATTERN, task_hrid), f"Поле 'hrid' имеет некорректный формат: {task_hrid}"

def get_member_profile(client, space_id):
    """Получение id пользователя который создает задачу"""
    resp = client.post(**get_profile_endpoint(space_id=space_id))
    resp.raise_for_status()
    return resp.json()["payload"]["profile"]["memberId"]

def create_task(client, payload):
    """Helper function to create task."""
    return client.post(**payload)

def get_client(request, client_fixture):
    """Получение клиента из тестового фикстура."""
    with allure.step(f"Получение клиента для {client_fixture}"):
        return request.getfixturevalue(client_fixture)