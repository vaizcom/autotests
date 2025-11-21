import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

SAMPLE_SIZE = 20  # сколько задач валидировать из ответа

@allure.title("GetTasks: Проверка структуры и типов полей задач в ответе")
def test_get_tasks_schema(owner_client, main_space, board_with_tasks):
    """
    Проверка структуры и типов полей задач только для owner_client.
    """
    with allure.step("owner_client: вызвать GetTasks с фильтром board"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space, limit=10000, board=board_with_tasks))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Проверить payload"):
        payload = resp.json().get("payload", {})
        assert "tasks" in payload and isinstance(payload["tasks"], list)
        tasks = payload["tasks"]

    if not tasks:
        with allure.step("Список задач пуст — проверку схемы пропускаем"):
            return

    with allure.step(f"Проверить схему для 20 задач из {len(tasks)}"):
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

        nullable_fields = {
            "archiver": (str, type(None)),
            "archivedAt": (str, type(None)),
            "parentTask": (str, type(None)),
            "dueEnd": (str, type(None)),
        }

        optional_fields = {"editor", "milestone", "dueStart", "completedAt", "deleter", "deletedAt"}

        for task in tasks:
            with allure.step(f"Валидация схемы для задачи '_id'={task.get('_id', 'unknown')}"):
                for field, expected_type in required_fields.items():
                    assert field in task, f"Отсутствует обязательное поле: {field}"
                    assert isinstance(task[field], expected_type), f"Поле {field} должно быть типа {expected_type}"

                for field, expected_types in nullable_fields.items():
                    if field in task:
                        assert isinstance(task[field], expected_types), f"Поле {field} имеет неверный тип"

                task_fields = set(task.keys())
                all_known_fields = set(required_fields.keys()) | set(nullable_fields.keys()) | optional_fields
                unexpected_fields = task_fields - all_known_fields
                assert not unexpected_fields, f"Найдены неожиданные поля: {unexpected_fields}"
