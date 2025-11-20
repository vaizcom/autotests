import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint
from test_backend.task_service.utils import get_member_profile

pytestmark = [pytest.mark.backend]

@allure.title("GetTasks: фильтр по creator")
@pytest.mark.parametrize(
    'client_fixture, expected_status, expected_name_prefix',
    [
        ('owner_client', 200, 'owner'),
        ('manager_client', 200, 'manager'),
        ('member_client', 200, 'member'),
        ('guest_client', 200, 'guest'),
        ('client_with_access_only_in_space',200, 'no_access_to_project'),
        ('client_with_access_only_in_project', 200, 'no_access_to_board'),
    ],
    ids=['creator: owner' , 'creator: manager', 'creator: member', 'creator: guest','creator: no_access_to_project', 'creator: no_access_to_board'],
)
def test_get_tasks_filtered_by_creator(request,owner_client, client_fixture, main_space, expected_status, expected_name_prefix, board_with_tasks_created_all_clients):
    allure.dynamic.title(
        f"GetTasks: фильтр по creator: creator={expected_name_prefix}_id, ожидаемый статус={expected_status}")
    client = request.getfixturevalue(client_fixture)

    with allure.step(f"Подготовка данных для {expected_name_prefix}: получить профиль участника и определить его creator_id"):
        member_id = get_member_profile(space_id=main_space, client=client)

    with allure.step(f"Вызвать GetTasks с фильтром creator: {expected_name_prefix}_id"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space, creator=member_id, board=board_with_tasks_created_all_clients))

    with allure.step(f"Проверить HTTP {expected_status}"):
        assert resp.status_code == expected_status

    with allure.step("Проверить response payload и фильтрацию по creator"):
        payload = resp.json().get("payload", {})
        assert "tasks" in payload and isinstance(payload["tasks"], list)
        tasks = payload["tasks"]

        for task in tasks:
            expected_name = f"{expected_name_prefix} Task Created"
            assert task.get("creator") == member_id, (
                f"Задача {task.get('_id', 'unknown')} имеет иного creator: {task.get('creator')}"
            )
            # Проверяем, что среди всех задач есть хотя бы одна с ожидаемым именем
            assert any(task.get("name") == expected_name for task in tasks), (
                f"В списке задач нет задачи с именем '{expected_name}'. "
                f"Доступные имена: {[t.get('name') for t in tasks]}"
        )

        if not tasks:
            with allure.step(
                    "Проверка что пустой список допустим для клиентов без доступа на уровне проекта/доски/гостя"):
                assert client_fixture in ('guest_client', 'client_with_access_only_in_space',
                                          'client_with_access_only_in_project'), (
                    f"Пустой список задач допустим только для ограниченных клиентов, но текущий клиент: {client_fixture}"
                )
            return
        assert all(t.get("creator") == member_id for t in tasks), "Обнаружены задачи с иным creator"


@allure.title("GetTasks: фильтр по creator — creator_id из no_access_to_project")
def test_get_tasks_filtered_by_unknown_creator(owner_client, main_space, board_with_tasks_created_all_clients):
    with allure.step("Вызвать GetTasks с несуществующим creator_id"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space, creator="non-existent-id-123", board=board_with_tasks_created_all_clients))
    with allure.step("Ожидаем 400, 'creator must be a mongodb id'"):
        body = resp.json()
        assert body.get("payload") is None
        error = body.get("error", {})
        assert error.get("code") == "InvalidForm"
        fields = error.get("fields", [])
        board_field = next((f for f in fields if f.get("name") == "creator"), None)
        codes = board_field.get("codes", [])
        assert "creator must be a mongodb id" in codes