import pytest
import allure
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

SAMPLE_SIZE = 20  # сколько задач валидировать из ответа

@allure.title("Тестирование получения задач(get_tasks) под разными ролями с валидацией набора полей и типов")
@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_get_tasks_access_by_role(request, client_fixture, expected_status, board_with_tasks, main_space):
    client = request.getfixturevalue(client_fixture)

    with allure.step(f"{client_fixture}: вызвать GetTasks"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_tasks))

    with allure.step(f"Проверить HTTP {expected_status}"):
        assert resp.status_code == expected_status

    if expected_status == 200:
        with allure.step("Проверить payload"):
            payload = resp.json().get("payload", {})
            assert "tasks" in payload and isinstance(payload["tasks"], list)
            tasks = payload["tasks"]

        if len(tasks) == 0:
            with allure.step("Список задач пустой - пропускаем проверку схемы"):
                return

        # Ограничиваем количество проверяемых задач
        sample = tasks[:SAMPLE_SIZE] if len(tasks) > SAMPLE_SIZE else tasks

        with allure.step(f"Проверить схему для {len(sample)} задач из {len(tasks)}"):
            # Обязательные поля и их типы
            required_fields = {
                "_id": str,
                "name": str,
                "group": str,
                "project": str,
                "priority": (int, float),
                "creator": str,
                "completed": bool,
                "assignees": list,
                "document": str,
                "createdAt": str,
                "updatedAt": str,
                "board": str,
                "types": list,
                "subtasks": list,
                "hrid": str,
                "leftConnectors": list,
                "rightConnectors": list,
                "customFields": list,
                "followers": dict,
                "milestones": list,
            }

            # Поля которые могут быть None
            nullable_fields = {
                "archiver": (str, type(None)),
                "archivedAt": (str, type(None)),
                "parentTask": (str, type(None)),
                "dueEnd": (str, type(None)),
            }

            # Опциональные поля
            optional_fields = {"editor", "milestone", "dueStart", "completedAt", "deleter", "deletedAt"}

            for task in sample:
                with allure.step(f"Проверить задачу {task.get('_id', 'unknown')}"):
                    # Проверяем все обязательные поля
                    for field, expected_type in required_fields.items():
                        assert field in task, f"Отсутствует обязательное поле: {field}"
                        assert isinstance(task[field],
                                          expected_type), f"Поле {field} должно быть типа {expected_type.__name__}"

                    # Проверяем nullable поля
                    for field, expected_types in nullable_fields.items():
                        if field in task:
                            assert isinstance(task[field], expected_types), f"Поле {field} имеет неверный тип"

                    # Проверяем что нет лишних полей (кроме известных опциональных)
                    task_fields = set(task.keys())
                    all_known_fields = set(required_fields.keys()) | set(nullable_fields.keys()) | optional_fields
                    unexpected_fields = task_fields - all_known_fields
                    assert not unexpected_fields, f"Найдены неожиданные поля: {unexpected_fields}"

        with allure.step("Проверить что задачи принадлежат правильному board"):
            for task in sample:
                assert task["board"] == str(board_with_tasks), f"Задача {task['_id']} принадлежит неправильному board"


@allure.title("Проверка что список задач пустой для пользователей которые не имеют доступ к борде")
@pytest.mark.parametrize(
    'client_fixture',
    ['client_with_access_only_in_space', 'client_with_access_only_in_project'],
    ids=['no_access_to_project', 'no_access_to_board'],
)
def test_get_tasks_limited_access(request, client_fixture, board_with_tasks, main_space):
    client = request.getfixturevalue(client_fixture)

    with allure.step(f"{client_fixture}: вызвать GetTasks"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_tasks))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Проверить что список задач пустой"):
        payload = resp.json().get("payload", {})
        assert "tasks" in payload and isinstance(payload["tasks"], list)
        assert len(payload["tasks"]) == 0, f"Ожидался пустой список задач для {client_fixture}"


@allure.title("Проверка что пользователь без доступа к спейсу не имеет доступ к задачам")
def test_get_tasks_no_access(request, board_with_tasks, main_space):
    client = request.getfixturevalue('foreign_client')

    with allure.step("foreign_client: вызвать GetTasks"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_tasks))

    with allure.step("Проверить HTTP 400"):
        assert resp.status_code == 400

# TODO: добавить кейс для пользователя у которого нет доступа к борде, роль-No access