import pytest
import allure

from tests.test_backend.data.endpoints.Task.task_endpoints import (
    get_task_endpoint,
    multiple_edit_tasks_endpoint,
)

pytestmark = [pytest.mark.backend]

@allure.parent_suite("multiple_edit_tasks")
@allure.title("Multiple edit Tasks: назначение assignees задачам в которой уже был установлен assignee и задаче без assignee")
def test_multiple_edit_tasks_assignees(owner_client, main_space, main_project, main_board, main_personal, make_task_in_main):
    """
    Создаём 2 задачи в одной борде: у первой уже стоит ассайни, у второй нет.
    Затем применяем multiple_edit_tasks_endpoint и проверяем,
    что у обеих задач установлен только переданный ассайни.
    """
    with allure.step("Определяем целевого ассайни"):
        # Берём один валидный id из фикстуры main_personal по указанной роли
        target_assignee = main_personal["member"][0]

    with allure.step("Создаём задачу №1 c заранее установленным ассайни"):
        task1 = make_task_in_main({
            "name": "Task with assignee",
            "assignees": main_personal["manager"][0],
        })
        task1_id = task1["_id"]

    with allure.step("Создаём задачу №2 без ассайни"):
        task2 = make_task_in_main({
            "name": "Task without assignee",
        })
        task2_id = task2["_id"]

    with allure.step("Массово обновляем ассайни у обеих задач"):
        payload = [
            {"taskId": task1_id, "assignees": target_assignee},
            {"taskId": task2_id, "assignees": target_assignee},
        ]
        resp_edit = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks=payload,
        ))
        assert resp_edit.status_code == 200, resp_edit.text

    with allure.step("Проверяем итоговые ассайни у задачи №1"):
        r1 = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task1_id))
        assert r1.status_code == 200, r1.text
        assignees_1 = r1.json()["payload"]["task"].get("assignees", [])
        assert assignees_1 == [target_assignee], f"Ожидался единственный ассайни {target_assignee}, получено {assignees_1}"

    with allure.step("Проверяем итоговые ассайни у задачи №2"):
        r2 = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task2_id))
        assert r2.status_code == 200, r2.text
        assignees_2 = r2.json()["payload"]["task"].get("assignees", [])
        assert assignees_2 == [target_assignee], f"Ожидался единственный ассайни {target_assignee}, получено {assignees_2}"