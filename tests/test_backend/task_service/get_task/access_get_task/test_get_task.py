import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.task_service.create_task.utils import get_client

pytestmark = [pytest.mark.backend]

@allure.title("Тестирование создания задачи разными пользовательскими ролями с минимальным набором полей."
              " Проверка полного совпадения набора ключей задачи и типов данных")
@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200),
        ('client_with_access_only_in_space', 400),
        ('client_with_access_only_in_project', 400),
        ('foreign_client', 403)
    ],
    ids=['owner', 'manager', 'member', 'guest','no_access_to_project', 'no_access_to_board', 'no_access_to_space'],
)
def test_get_task(request, main_space, board_with_tasks, client_fixture, expected_status, main_project):
    """
    Тест проверки получения задачи под разными ролями с валидацией набора полей и типов.
    """
    allure.dynamic.title(
        f"Get task: клиент={client_fixture}, ожидаемый статус={expected_status}")

    client = get_client(request, client_fixture)
    slug_id = 'CCSS-13258'
    # to do: сделать рандом slug от getTasks
    # to do: сделать по таск Id


    with allure.step("Получение задачи"):
        response = client.post(**get_task_endpoint(space_id=main_space, slug_id=slug_id))

    # Проверяем статус ответа
    with allure.step(f"Проверка статус-кода: ожидаем {expected_status}"):
        assert response.status_code == expected_status, response.text

    # Если запрос успешен, валидируем структуру и типы
    if response.status_code == 200:
        with allure.step("Проверяем содержимое ответа с задачей"):
            body = response.json()

            # Верхний уровень ответа
            assert "payload" in body and isinstance(body["payload"], dict), "Ошибка: отсутствует/некорректен ключ 'payload'"
            assert "task" in body["payload"] and isinstance(body["payload"]["task"], dict), "Ошибка: отсутствует/некорректен ключ 'payload.task'"
            assert "type" in body and isinstance(body["type"], str), "Ошибка: отсутствует/некорректен ключ 'type'"

            task = body["payload"]["task"]

            # Ожидаемые ключи и типы
            expected_schema = {
                # строки
                "_id": str,
                "name": str,
                "group": str,
                "board": str,
                "project": str,
                "hrid": str,
                "creator": str,
                "createdAt": str,
                "updatedAt": str,
                "document": str,
                "editor": str,
                "milestone": str,

                # допускают None или строку
                "parentTask": (str, type(None)),
                "archiver": (str, type(None)),
                "dueStart": (str, type(None)),
                "dueEnd": (str, type(None)),
                "archivedAt": (str, type(None)),
                "completedAt": (str, type(None)),
                "deleter": (str, type(None)),
                "deletedAt": (str, type(None)),

                # булево
                "completed": bool,

                # числа
                "priority": int,

                # массивы
                "types": list,
                "assignees": list,
                "subtasks": list,
                "milestones": list,
                "rightConnectors": list,
                "leftConnectors": list,
                "customFields": list,

                # словари
                "followers": dict,
            }

            # Проверяем, что набор ключей совпадает ровно
            with allure.step("Проверка полного совпадения набора полей задачи"):
                actual_keys = set(task.keys())
                expected_keys = set(expected_schema.keys())
                missing = expected_keys - actual_keys
                extra = actual_keys - expected_keys
                assert not missing, f"Отсутствуют обязательные поля: {sorted(missing)}"
                assert not extra, f"Найдены лишние поля: {sorted(extra)}"

            # Проверка типов по схеме
            with allure.step("Проверка типов данных всех полей задачи"):
                for field, expected_type in expected_schema.items():
                    value = task[field]
                    assert isinstance(value, expected_type), (
                        f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
                    )

            # Дополнительные уточнения по элементам коллекций
            with allure.step("Дополнительные проверки содержимого коллекций"):
                # Массивы строк
                list_of_strings_fields = [
                    "assignees", "subtasks", "milestones",
                    "rightConnectors", "leftConnectors", "types", "customFields"
                ]
                for f in list_of_strings_fields:
                    assert isinstance(task[f], list), f"Поле '{f}' должно быть массивом"
                    assert all(isinstance(x, str) for x in task[f]), f"Элементы поля '{f}' должны быть строками"

                # followers: ключи и значения строки
                assert all(isinstance(k, str) for k in task["followers"].keys()), "Ключи 'followers' должны быть строками"
                assert all(isinstance(v, str) for v in task["followers"].values()), "Значения 'followers' должны быть строками"

            # Несколько бизнес-проверок значения (по возможности стабильных)
            with allure.step("Бизнес-проверки стабильных значений"):
                # соответствие известным контекстным ID
                assert task["board"] == board_with_tasks, "Ошибка: неверное значение поля 'board'"
                assert task["project"] == main_project, "Ошибка: неверное значение поля 'project'"

    else:
        task_err = response.json()["error"]
        assert task_err['code'] in ['AccessDenied', 'NotFound']