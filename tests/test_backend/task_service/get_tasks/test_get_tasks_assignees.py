import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.title("GetTasks assignees: пустой массив — без фильтра по исполнителям")
def test_get_tasks_assignees_empty(owner_client, main_space, board_with_tasks):
    with allure.step("Выполнить POST /GetTasks с assignees=[]"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            assignees=[]
        ))
    with allure.step("Проверить HTTP 200 и наличие массива tasks"):
        assert response.status_code == 200
        data = response.json().get("payload", {})
        tasks = data.get("tasks", [])
        assert isinstance(tasks, list)


@allure.title("GetTasks assignees: один валидный исполнитель")
def test_get_tasks_assignees_single_member(owner_client, main_space, board_with_tasks, main_personal):
    member_id = main_personal["member"][0]
    with allure.step("Выполнить POST /GetTasks с assignees=[member]"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            assignees=[member_id]
        ))
    with allure.step("Проверить HTTP 200 и массив tasks"):
        assert response.status_code == 200
        data = response.json().get("payload", {})
        tasks = data.get("tasks", [])
        assert isinstance(tasks, list)
    with allure.step(f"Проверить наличие переданного исполнителя (в массиве) в первых 20 задачах"):
        to_check = tasks[:20] if len(tasks) > 20 else tasks
        for task in to_check:
            assignees = task.get("assignees", [])
            assert member_id in assignees

@allure.title("GetTasks assignees: несколько валидных исполнителей (OR-фильтр)")
def test_get_tasks_assignees_multiple_members(owner_client, main_space, board_with_tasks, main_personal):
    member_1 = main_personal["member"][0]
    member_2 = main_personal["manager"][0]
    with allure.step("Выполнить POST /GetTasks с assignees=[member_1, member_2]"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            assignees=[member_1, member_2]
        ))
    with allure.step("Проверить HTTP 200 и массив tasks"):
        assert response.status_code == 200
        data = response.json().get("payload", {})
        tasks = data.get("tasks", [])
        assert isinstance(tasks, list)
    with allure.step(f"Проверить что хотябы один из двух переданных исполнителей(OR-фильтр) присутствует в первых 20 задачах"):
        to_check = tasks[:20] if len(tasks) > 20 else tasks
        for task in to_check:
            assignees = task.get("assignees", [])
            assert member_1 in assignees or member_2 in assignees


@allure.title("GetTasks assignees: если указать пользователя невалидного(из другой борды) — ожидаем пустой список задач")
def test_get_tasks_assignees_user_without_access(owner_client, main_space, board_with_tasks, temp_member):
    user_without_access = temp_member
    with allure.step("Выполнить POST /GetTasks от пользователя без доступа к борде"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            assignees=[user_without_access]
        ))
    with allure.step("Проверить HTTP 200 и пустой массив tasks при запросе с assignees= user_without_access"):
        assert response.status_code == 200
        data = response.json().get("payload", {})
        tasks = data.get("tasks", [])
        assert isinstance(tasks, list)
        assert tasks == []