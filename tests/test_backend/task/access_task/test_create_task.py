from datetime import datetime, timedelta
import random

import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, delete_task_endpoint
from test_backend.task.utils import validate_hrid, get_client, get_member_profile, create_task, get_type, get_group, \
    get_current_timestamp, get_due_end, get_priority, get_assignee, get_milestone, assert_task_keys

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
def test_create_task_with_minimal_payload(request, main_space, main_board, client_fixture, expected_status, main_project):
    """
    Тест проверки создания задачи с минимальным набором полей в системе управления проектами под разными ролями.

    Цель теста — убедиться, что можно успешно создать задачу, указав только минимально необходимые данные, и что поведение API зависит от прав пользователя (типа клиента).
    В процессе теста дополнительно валидируются структура созданной задачи, значения по умолчанию, связи (creator, board и пр.), а также удаление задачи после проверки.

    Ход теста:
        1. Получение клиента согласно переданной роли через фикстуру.
        2. Получение id пользователя, с помощью которого осуществляется создание задачи.
        3. Формирование минимального payload и попытка создать задачу через API.
        4. Проверка статус-кода ответа.
        5. Если задача успешно создана (ответ 200):
            - Проверка наполнения и структуры ответа
    """
    allure.dynamic.title(
        f"Create task with minimal payload: клиент={client_fixture}, ожидаемый статус={expected_status}")

    with allure.step(f"Получение клиента для {client_fixture}"):
        client = get_client(request, client_fixture)

    with allure.step(f"Получение id пользователя который создает задачу"):
        member_id = get_member_profile(client, main_space)

    task_id = None  # переменную объявляем до блока try

    try:

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
                task_id = task["_id"]

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
                        validate_hrid(client, main_space, main_project, task["hrid"])

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
                    assert task["followers"] == {member_id: "creator"}, "Ошибка: 'followers' должно включать creator"
                    assert isinstance(task["rightConnectors"], list) and len(task["rightConnectors"]) == 0, \
                        "Ошибка: 'rightConnectors' должно быть пустым списком"
                    assert isinstance(task["leftConnectors"], list) and len(task["leftConnectors"]) == 0, \
                        "Ошибка: 'leftConnectors' должно быть пустым списком"

                with allure.step("Проверяем содержимое ответа задачи"):
                    task = response.json()["payload"]["task"]

                    with allure.step("Проверка структуры ключей задачи"):
                        expected_task_keys = {
                            "name", "group", "board", "project", "parentTask", "priority", "completed",
                            "types", "assignees", "milestones", "subtasks", "dueStart", "dueEnd",
                            "_id", "createdAt", "updatedAt", "document", "milestone", "followers",
                            "hrid", "rightConnectors", "leftConnectors", "archiver", "archivedAt",
                            "completedAt", "deleter", "deletedAt", "customFields", "creator"
                        }
                        assert_task_keys(task, expected_task_keys)
    finally:
        if task_id:
            with allure.step(f"Удаляем задачу: {task_id}"):
                del_resp = client.post(**delete_task_endpoint(task_id=task_id, space_id=main_space))
                assert del_resp.status_code == 200, (
                    f"Не удалось удалить задачу {task_id}: {del_resp.status_code} {del_resp.text}"
                )


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
    Данный тест проверяет возможность создания задачи с заранее определённым набором данных (payload) через API
     управления задачами для различных ролей пользователей, а также корректность и полноту возвращаемого ответа.
     Тест эмулирует действия разных типов клиентов (владелец, менеджер, участник, гость) и сравнивает фактический результат с ожидаемым HTTP-статусом.
    """
    allure.dynamic.title(
        f"Проверка создания задачи с конкретным payload и структурой ответа : клиент={client_fixture}, ожидаемый статус={expected_status}"
    )

    # Получение клиента
    with allure.step(f"Получение клиента для {client_fixture}"):
        client = get_client(request, client_fixture)

    # Формируем имя задачи с учетом пользователя и текущей даты
    task_name = f"Create task клиент={client_fixture}, дата={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # Получение профиля для извлечения creator ID
    with allure.step(f"Получение профиля для извлечения creator ID"):
        member_id = get_member_profile(client, main_space)

    with allure.step("Получаем случайный type из борды"):
        random_type_id = get_type(client, main_board, main_space)

    with allure.step("Получаем случайную группу из борды"):
        random_group_id = get_group(client, main_board, main_space)

    with allure.step("Получаем текущую дату и время в формате ISO 8601 UTC"):
        current_timestamp = get_current_timestamp()

    with allure.step("Прибавляем неделю к переданному времени в формате ISO 8601 UTC"):
        due_end = get_due_end()

    with allure.step("Получаем случайную priority"):
        priority = get_priority()

    with allure.step("Получаем random_member_id для извлечения assignees"):
        random_member_id = get_assignee(client, main_space)

    with allure.step("Получаем get_random_complete для извлечения completed"):
        get_random_complete = random.choice([True, False])

    with allure.step("Получаем get_random_complete для извлечения completed"):
        get_random_milestone = get_milestone(client, main_space, main_board)

    # Если запрос успешен, проверяем содержимое ответа
    task_id = None

    try:

        # Формируем payload
        with allure.step("Генерация payload"):
            payload = create_task_endpoint(
                space_id=main_space,
                board=main_board,
                name=task_name,
                types=[random_type_id],
                assignees= random_member_id,
                due_start=current_timestamp,
                due_end= due_end,
                priority=priority,
                completed=get_random_complete,
                group=random_group_id,
                milestones=[get_random_milestone],
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
                task_id = task["_id"]

                # Проверка основных полей задачи
                with allure.step("Проверяем основные данные задачи"):
                    assert task["name"] == task_name, "Ошибка: неверное имя задачи"
                    assert task["group"] == random_group_id, "Ошибка: неверная группа задачи"
                    assert task["board"] == main_board, "Ошибка: неверное значение board задачи"
                    assert task["project"] == main_project, "Ошибка: неверный проект"
                    assert task["parentTask"] is None, "Ошибка: поле parentTask должно быть None"
                    assert task["priority"] == priority, "Ошибка: неверный приоритет задачи"
                    assert task["completed"] == get_random_complete, "Ошибка: задача должна быть помечена как завершённая"
                    assert task["creator"] == member_id, "Ошибка: 'creator' не соответствует memberId пользователя"

                # Проверка полей, относящихся к работе
                with allure.step("Проверяем связанные поля"):
                    assert task["types"] == [random_type_id], "Ошибка: неверное значение types"
                    assert task["assignees"] == [random_member_id], "Ошибка: неверное значение assignees"
                    assert task["milestones"] == [get_random_milestone], "Ошибка: неверное значение milestones"
                    assert task["subtasks"] == [], "Ошибка: поле с подзадачами должно быть пустым"

                # Проверка временных полей
                with allure.step("Проверяем временные поля и сроки задачи"):
                    assert task["dueStart"] == current_timestamp.replace("+00:00", "Z"), "Ошибка: неверное значение dueStart"
                    assert task["dueEnd"] == due_end.replace("+00:00", "Z"), "Ошибка: неверное значение dueEnd"

                # Проверка метаданных и системных полей
                with allure.step("Проверяем метаданные"):
                    assert "_id" in task, "Ошибка: отсутствует поле '_id'"
                    assert task["createdAt"] is not None, "Ошибка: поле 'createdAt' должно быть задано"
                    assert task["updatedAt"] is not None, "Ошибка: поле 'updatedAt' должно быть задано"
                    assert task["document"] is not None, "Ошибка: неверный документ"
                    assert task["milestone"] == get_random_milestone, "Ошибка: неверный milestone"
                    assert task["followers"] == {member_id: "creator"}, "Ошибка: 'followers' должно включать creator"

                # Проверка корректности формата `hrid`
                with allure.step("Проверяем поле 'hrid'"):
                    assert "hrid" in task, "Поле 'hrid' отсутствует"
                    validate_hrid(client, main_space, main_project, task["hrid"])

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

                with allure.step("Проверяем содержимое ответа задачи"):
                    task = response.json()["payload"]["task"]

                    with allure.step("Проверка структуры ключей задачи"):
                        expected_task_keys = {
                            "name", "group", "board", "project", "parentTask", "priority", "completed",
                            "types", "assignees", "milestones", "subtasks", "dueStart", "dueEnd",
                            "_id", "createdAt", "updatedAt", "document", "milestone", "followers",
                            "hrid", "rightConnectors", "leftConnectors", "archiver", "archivedAt",
                            "completedAt", "deleter", "deletedAt", "customFields", "creator"
                        }
                        assert_task_keys(task, expected_task_keys)

    finally:
        if task_id:
            with allure.step(f"Удаляем задачу: {task_id}"):
                del_resp = client.post(**delete_task_endpoint(space_id=main_space, task_id=task_id))
                assert del_resp.status_code == 200, (
                    f"Не удалось удалить задачу {task_id}: {del_resp.status_code} {del_resp.text}"
                )


