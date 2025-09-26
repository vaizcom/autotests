import re

import random
import allure

from datetime import datetime, timedelta

from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.data.endpoints.Project.project_endpoints import get_project_endpoint
from test_backend.data.endpoints.User.profile_endpoint import get_profile_endpoint
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from test_backend.data.endpoints.milestone.milestones_endpoints import get_milestones_endpoint


def validate_hrid(client, space_id, project_id, task_hrid):
    """
    Проверяет, что hrid соответствует формату <slug>-<число>.
    """
    # Проверяем, что клиент является объектом APIClient
    assert hasattr(client, 'post'), "Клиент должен быть экземпляром APIClient"

    with allure.step(f"Получаем slug проекта"):
        response = client.post(**get_project_endpoint(project_id=project_id, space_id=space_id))
        response.raise_for_status()

        # Получаем slug проекта
        project_slug = response.json().get("payload", {}).get("project", {}).get("slug", None)
        assert project_slug, "Ошибка: не удалось получить slug проекта"

    # Проверяем, что hrid соответствует формату <slug>-<число>
    hrid_pattern = rf"^{project_slug}-\d+$"
    with allure.step(f"Проверка, что hrid '{task_hrid}' соответствует шаблону '{hrid_pattern}'"):
        assert re.match(hrid_pattern, task_hrid), f"Поле 'hrid' имеет некорректный формат: {task_hrid}"

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


def get_type(client, board_id, space_id):
    """
    Получение случайного `_id` из typesList борды.
    """
    with allure.step(f"Запрашиваем данные борды с ID: {board_id}"):
        response = client.post(**get_board_endpoint(board_id=board_id, space_id=space_id))
        response.raise_for_status()

    board_data = response.json().get("payload", {}).get("board", {})
    types_list = board_data.get("typesList", [])

    with allure.step("Проверяем наличие typesList"):
        assert types_list, "Ошибка: typesList пуст или не существует."

    with allure.step("Рандомно выбираем `type` из typesList"):
        random_type = random.choice(types_list)
        return random_type["_id"]


def get_group(client, board_id, space_id):
    """
    Получение случайного `_id` группы из списка groups борды.
    """
    with allure.step(f"Запрашиваем данные борды с ID: {board_id}"):
        response = client.post(**get_board_endpoint(board_id=board_id, space_id=space_id))
        response.raise_for_status()

    board_data = response.json().get("payload", {}).get("board", {})
    groups = board_data.get("groups", [])

    with allure.step("Проверяем наличие списка групп"):
        assert groups, "Ошибка: groups пуст или не существует."

    with allure.step("Рандомно выбираем группу из списка"):
        random_group = random.choice(groups)
        return random_group["_id"]


def get_current_timestamp():
    """
    Возвращает текущую дату и время в формате "YYYY-MM-DDTHH:MM:SS.sss+00:00".
    :return: строка с датой и временем.
    """
    current_time = datetime.utcnow()
    return current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"

def get_due_end():
    """
    Возвращает дату и время через неделю от текущего момента в формате "YYYY-MM-DDTHH:MM:SS.sss+00:00".
    :return: строка с датой и временем.
    """
    current_time = datetime.utcnow()
    due_end = current_time + timedelta(weeks=1)
    return due_end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"

def get_priority():
    """
    Возвращает случайный priority от 0 до 3.
    """
    return random.randint(0, 3)

def get_assignee(client, space_id):
    """
    Возвращает случайный member_id из списка участников пространства (space).
    :return: случайный member_id
    """
    # Делаем запрос к endpoint для получения списка участников
    response = client.post(**get_space_members_endpoint(space_id))
    response.raise_for_status()  # Поднимаем исключение, если статус код != 2xx

    # Извлекаем список участников
    members = response.json().get("payload", {}).get("members", [])
    assert members, "Ошибка: список участников пуст или недоступен"

    # Фильтруем список, исключая участника с nickName "automation_bot"
    filtered_members = [member for member in members if member.get("nickName") != "automation_bot"]
    assert filtered_members, "Ошибка: после фильтрации список участников пуст"

    # Рандомно выбираем member_id из отфильтрованного списка
    random_member = random.choice(filtered_members)
    return random_member["_id"]


def get_milestone(client, space_id, board_id):
    """
    Получает список майлстоунов из указанной борды и возвращает случайный milestone_id.
    :return: Случайный идентификатор майлстоуна.
    """
    # Делаем запрос к эндпоинту для получения майлстоунов
    response = client.post(**get_milestones_endpoint(space_id=space_id, board_id=board_id))
    response.raise_for_status()  # Проверяем успешность запроса

    # Извлекаем список майлстоунов
    milestones = response.json().get("payload", {}).get("milestones", [])
    assert milestones, "Ошибка: список майлстоунов пуст или недоступен"

    # Возвращаем случайный milestone_id
    random_milestone = random.choice(milestones)
    return random_milestone["_id"]
