from datetime import datetime

import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint
from test_backend.task.utils import validate_hrid, get_client, get_member_profile, create_task

pytestmark = [pytest.mark.backend]

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
    allure.dynamic.title(
        f"Create task with minimal payload: клиент={client_fixture}, ожидаемый статус={expected_status}")

    with allure.step(f"Получение клиента для {client_fixture}"):
        client = get_client(request, client_fixture)

    with allure.step(f"Получение id пользователя который создает задачу"):
        member_id = get_member_profile(client, main_space)

    with allure.step("Создание задачи с минимальным payload"):
        payload = create_task_endpoint(space_id=main_space, board=main_board)
        response = create_task(client, payload)

    # Проверяем статус ответа
    with allure.step(f"Проверка статус-кода: ожидаем {expected_status}"):
        assert response.status_code == expected_status, response.text

    # Если запрос успешен, проверяем содержимое ответа
    if response.status_code == 200:
        with allure.step("Проверяем содержимое ответа с задачей"):
            task = response.json()["payload"]["task"]

            with allure.step("Проверка обязательных полей"):
                assert task["board"] == main_board, "Ошибка: неверное значение поля 'board'"
                assert task["name"] == "Untitled task", "Ошибка: неверное значение поля 'name'"
                assert task["completed"] is False, "Ошибка: поле 'completed' должно быть False"
                assert task["creator"] == member_id, "Ошибка: 'creator' не соответствует memberId пользователя"

            with allure.step("Проверка системных полей"):
                assert "_id" in task, "Ошибка: отсутствует поле '_id'"
                assert task["createdAt"] is not None, "Ошибка: поле 'createdAt' должно быть задано"
                assert task["updatedAt"] is not None, "Ошибка: поле 'updatedAt' должно быть задано"

            # Проверка корректности формата `hrid`
            with allure.step("Проверяем поле 'hrid'"):
                assert "hrid" in task, "Поле 'hrid' отсутствует"
                validate_hrid(task["hrid"])

            with allure.step("Проверка полей, которые должны быть пустыми"):
                assert task["assignees"] == [], "Ошибка: 'assignees' должно быть пустым списком"
                assert task["types"] == [], "Ошибка: 'types' должно быть пустым списком"
                assert task["milestones"] == [], "Ошибка: 'milestones' должно быть пустым списком"
                assert task["subtasks"] == [], "Ошибка: 'subtasks' должно быть пустым списком"

            with allure.step("Проверка полей с `None` (null)"):
                assert task["parentTask"] is None, "Ошибка: 'parentTask' должно быть None"
                assert task["archiver"] is None, "Ошибка: 'archiver' должно быть None"
                assert task["archivedAt"] is None, "Ошибка: 'archivedAt' должно быть None"
                assert task["completedAt"] is None, "Ошибка: 'completedAt' должно быть None"

            with allure.step("Проверка значений по умолчанию"):
                assert task["priority"] == 1, "Ошибка: 'priority' должно быть равно 1"
                assert isinstance(task["followers"], dict), "Ошибка: 'followers' должно быть словарем"
                assert task["followers"].get(member_id) == "creator", "Ошибка: 'followers' должно включать creator"
                assert isinstance(task["rightConnectors"], list) and len(task["rightConnectors"]) == 0, \
                    "Ошибка: 'rightConnectors' должно быть пустым списком"
                assert isinstance(task["leftConnectors"], list) and len(task["leftConnectors"]) == 0, \
                    "Ошибка: 'leftConnectors' должно быть пустым списком"


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
def test_create_task_with_specific_payload_and_response(
        request, client_fixture, expected_status, main_space, main_board, main_project
):
    """
    Проверка создания задачи с конкретным payload и структурой ответа.
    """
    allure.dynamic.title(
        f"Create task with specific payload and validate response: клиент={client_fixture}, ожидаемый статус={expected_status}"
    )

    # Получение клиента
    with allure.step(f"Получение клиента для {client_fixture}"):
        client = get_client(request, client_fixture)

    # Формируем имя задачи с учетом пользователя и текущей даты
    task_name = f"Create task клиент={client_fixture}, дата={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # Получение профиля для извлечения creator ID
    with allure.step(f"Получение профиля для извлечения creator ID"):
        member_id = get_member_profile(client, main_space)

    # Формируем payload
    with allure.step("Генерация payload"):
        payload = create_task_endpoint(
            space_id=main_space,
            board=main_board,
            name=task_name,
            types=["6866731185fb8d104544e82b"],
            assignees=["6866309d85fb8d104544a620"],
            due_start="2025-09-19T14:47:17.596+00:00",
            due_end="2026-09-19T14:47:17.596+00:00",
            priority=3,
            completed=True,
            group="6866731185fb8d104544e828",
            milestones=["68d5189654c332d6918a9b52"],
            parent_task=None,
            index=2
        )

    # Отправляем запрос
    with allure.step("Отправляем запрос на создание задачи"):
        response = client.post(**payload)

    # Проверяем статус ответа
    with allure.step(f"Проверка статус-кода: ожидаем {expected_status}"):
        assert response.status_code == expected_status, response.text

    # Если запрос успешен, проверяем содержимое ответа
    if response.status_code == 200:
        with allure.step("Проверяем содержимое ответа задачи"):
            task = response.json()["payload"]["task"]

            # Проверка основных полей задачи
            with allure.step("Проверяем основные данные задачи"):
                assert task["name"] == task_name, "Ошибка: неверное имя задачи"
                assert task["group"] == "6866731185fb8d104544e828", "Ошибка: неверная группа задачи"
                assert task["board"] == main_board, "Ошибка: неверное значение board задачи"
                assert task["project"] == main_project, "Ошибка: неверный проект"
                assert task["parentTask"] is None, "Ошибка: поле parentTask должно быть None"
                assert task["priority"] == 3, "Ошибка: неверный приоритет задачи"
                assert task["completed"] is True, "Ошибка: задача должна быть помечена как завершённая"

            # Проверка полей, относящихся к работе
            with allure.step("Проверяем связанные поля"):
                assert task["types"] == ["6866731185fb8d104544e82b"], "Ошибка: неверное значение types"
                assert task["assignees"] == ["6866309d85fb8d104544a620"], "Ошибка: неверное значение assignees"
                assert task["milestones"] == ["68d5189654c332d6918a9b52"], "Ошибка: неверное значение milestones"
                assert task["subtasks"] == [], "Ошибка: поле с подзадачами должно быть пустым"

            # Проверка временных полей
            with allure.step("Проверяем временные поля и сроки задачи"):
                assert task["dueStart"] == "2025-09-19T14:47:17.596Z", "Ошибка: неверное значение dueStart"
                assert task["dueEnd"] == "2026-09-19T14:47:17.596Z", "Ошибка: неверное значение dueEnd"

            # Проверка метаданных и системных полей
            with allure.step("Проверяем метаданные"):
                assert "_id" in task, "Ошибка: отсутствует поле '_id'"
                assert task["createdAt"] is not None, "Ошибка: поле 'createdAt' должно быть задано"
                assert task["updatedAt"] is not None, "Ошибка: поле 'updatedAt' должно быть задано"
                assert task["document"] is not None, "Ошибка: неверный документ"
                assert task["milestone"] == "68d5189654c332d6918a9b52", "Ошибка: неверный milestone"
                assert task["followers"].get(member_id) == "creator", "Ошибка: 'followers' должно включать creator"

            # Проверка корректности формата `hrid`
            with allure.step("Проверяем поле 'hrid'"):
                assert "hrid" in task, "Поле 'hrid' отсутствует"
                validate_hrid(task["hrid"])

            # Проверка пустых и None полей
            with allure.step("Проверяем поля с пустыми значениями и None"):
                assert task["rightConnectors"] == [], "Ошибка: поле rightConnectors должно быть пустым"
                assert task["leftConnectors"] == [], "Ошибка: поле leftConnectors должно быть пустым"
                assert task["archiver"] is None, "Ошибка: значение archiver должно быть None"
                assert task["archivedAt"] is None, "Ошибка: поле archivedAt должно быть None"
                assert task["completedAt"] is None, "Ошибка: поле completedAt должно быть None"
                assert task["deleter"] is None, "Ошибка: поле deleter должно быть None"
                assert task["deletedAt"] is None, "Ошибка: поле deletedAt должно быть None"
                assert task["customFields"] == [], "Ошибка: поле customFields должно быть пустым"