import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint
from test_backend.data.endpoints.User.profile_endpoint import get_profile_endpoint


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_create_task_with_minimal_payload(request, main_space, main_board, client_fixture, expected_status):
    """
    Проверка создания задачи только с минимальным набором данных (обязательные поля).
    """
    allure.dynamic.title(
        f"Create task with minimal payload: клиент={client_fixture}, ожидаемый статус={expected_status}")

    # Получение клиента
    with allure.step(f"Получение клиента для {client_fixture}"):
        client = request.getfixturevalue(client_fixture)

    # Получение профиля для извлечения creator ID
    with allure.step(f"Отправка запроса на получение профиля в space_id={main_space}"):
        resp = client.post(**get_profile_endpoint(space_id=main_space))
        resp.raise_for_status()
        member_id = resp.json()["payload"]["profile"]["memberId"]

    # Формируем минимальный пейлоад
    with allure.step("Формируем минимальный payload"):
        payload = create_task_endpoint(space_id=main_space, board=main_board)

    # Отправляем запрос
    with allure.step("Отправляем запрос на создание задачи"):
        response = client.post(**payload)

    # Проверяем статус ответа
    with allure.step(f"Проверка статус-кода: ожидаем {expected_status}"):
        assert response.status_code == expected_status, response.text

    # Если запрос успешен, проверяем содержимое ответа
    if response.status_code == 200:
        with allure.step("Проверяем содержимое ответа с задачей"):
            task = response.json()["payload"]["task"]

            # Проверка обязательных полей
            assert task["board"] == main_board, "Ошибка: неверное значение поля 'board'"
            assert task["name"] == "Untitled task", "Ошибка: неверное значение поля 'name'"
            assert task["completed"] is False, "Ошибка: поле 'completed' должно быть False"
            assert task["creator"] == member_id, "Ошибка: 'creator' не соответствует memberId пользователя"

            # Проверка системных полей
            assert "_id" in task, "Ошибка: отсутствует поле '_id'"
            assert task["createdAt"] is not None, "Ошибка: поле 'createdAt' должно быть задано"
            assert task["updatedAt"] is not None, "Ошибка: поле 'updatedAt' должно быть задано"

            # Проверка корректности формата `hrid`
            with allure.step("Проверяем поле 'hrid'"):
                assert "hrid" in task, "Поле 'hrid' отсутствует"
                # Проверяем, что hrid соответствует формату <префикс>-<число>
                import re
                hrid_pattern = r"^[A-Z]+-\d+$"
                assert re.match(hrid_pattern, task["hrid"]), f"Поле 'hrid' имеет некорректный формат: {task['hrid']}"

            # Проверка полей, которые должны быть пустыми
            assert task["assignees"] == [], "Ошибка: 'assignees' должно быть пустым списком"
            assert task["types"] == [], "Ошибка: 'types' должно быть пустым списком"
            assert task["milestones"] == [], "Ошибка: 'milestones' должно быть пустым списком"
            assert task["subtasks"] == [], "Ошибка: 'subtasks' должно быть пустым списком"

            # Проверка полей с `None` (null)
            assert task["parentTask"] is None, "Ошибка: 'parentTask' должно быть None"
            assert task["archiver"] is None, "Ошибка: 'archiver' должно быть None"
            assert task["archivedAt"] is None, "Ошибка: 'archivedAt' должно быть None"
            assert task["completedAt"] is None, "Ошибка: 'completedAt' должно быть None"

            # Проверка значений по умолчанию
            assert task["priority"] == 1, "Ошибка: 'priority' должно быть равно 1"
            assert isinstance(task["followers"], dict), "Ошибка: 'followers' должно быть словарем"
            assert task["followers"].get(member_id) == "creator", "Ошибка: 'followers' должно включать creator"
            assert isinstance(task["rightConnectors"], list) and len(task["rightConnectors"]) == 0, \
                "Ошибка: 'rightConnectors' должно быть пустым списком"
            assert isinstance(task["leftConnectors"], list) and len(task["leftConnectors"]) == 0, \
                "Ошибка: 'leftConnectors' должно быть пустым списком"
