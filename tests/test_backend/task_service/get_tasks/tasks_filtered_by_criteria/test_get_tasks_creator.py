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
    ],
    ids=['creator: owner' , 'creator: manager', 'creator: member', 'creator: guest'],
)
def test_get_tasks_filtered_by_creator(request, member_client, client_fixture, main_space, expected_status, expected_name_prefix, board_with_tasks_created_all_clients):
    allure.dynamic.title(
        f"GetTasks: фильтр по creator: creator={expected_name_prefix}_id, ожидаемый статус={expected_status}")
    client = request.getfixturevalue(client_fixture)

    with allure.step(f"Подготовка данных для {expected_name_prefix}: получить профиль участника и определить его creator_id"):
        member_id = get_member_profile(space_id=main_space, client=client)

    with allure.step(f"Вызвать GetTasks с фильтром creator: {expected_name_prefix}_id"):
        resp = member_client.post(**get_tasks_endpoint(space_id=main_space, creator=member_id, board=board_with_tasks_created_all_clients))

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
                    "Проверка что пустой список допустим для гостя, который может просматривать и не может создавать таски"):
                assert client_fixture =='guest_client', (
                    f"Пустой список задач допустим только для ограниченных клиентов, но текущий клиент: {client_fixture}"
                )
            return
        assert all(t.get("creator") == member_id for t in tasks), "Обнаружены задачи с иным creator"

@allure.title("GetTasks: фильтр по creator — ограниченные уровни доступа (space/project)")
@pytest.mark.parametrize(
    'client_fixture, expected_status, expected_name_prefix',
    [
        ('client_with_access_only_in_space', 200, 'no_access_to_project'),
        ('client_with_access_only_in_project', 200, 'no_access_to_board'),
    ],
    ids=['space_only_access', 'project_only_access'],
)
def test_get_tasks_creator_limited_access(
    request,
    client_fixture,
    expected_status,
    expected_name_prefix,
    main_space,
    member_client,
    board_with_tasks_created_all_clients,
):
    allure.dynamic.title(
        f"GetTasks: фильтр по creator — {expected_name_prefix} (ожидаемый HTTP {expected_status})"
    )

    client = request.getfixturevalue(client_fixture)

    with allure.step("Получить creator_id в рамках пространства"):
        member_id = get_member_profile(space_id=main_space, client=client)

    with allure.step("Вызвать GetTasks с фильтром creator на доске, к которой нет полного доступа"):
        resp = member_client.post(**get_tasks_endpoint(
            space_id=main_space,
            creator=member_id,
            board=board_with_tasks_created_all_clients
        ))

    with allure.step(f"Проверить HTTP {expected_status} и отсутствие задач (нет прав на проект/доску)"):
        assert resp.status_code == expected_status
        payload = resp.json().get("payload", {})
        tasks = payload.get("tasks", [])
        assert isinstance(tasks, list)
        assert not tasks, "Ожидался пустой список задач при ограниченных правах доступа"

@allure.title("GetTasks: фильтр по creator — creator_id из non-existent-id")
def test_get_tasks_filtered_non_existent_creator(owner_client, main_space, board_with_tasks_created_all_clients):
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



@allure.title("GetTasks: фильтр по creator — 2 валидных id - HTTP 400, допускается фильтрация только по одному creator")
def test_get_tasks_creator_two_valid_ids(
    main_space,
    owner_client,
    member_client,
    board_with_tasks_created_all_clients,
):
    with allure.step("Получить два валидных creator_id (owner, member)"):
        owner_id = get_member_profile(space_id=main_space, client=owner_client)
        member_id = get_member_profile(space_id=main_space, client=member_client)
        creators = [owner_id, member_id]

    with allure.step("Вызвать GetTasks с фильтром по двум creator_id"):
        resp = member_client.post(**get_tasks_endpoint(
            space_id=main_space,
            creator=creators,
            board=board_with_tasks_created_all_clients
        ))
    with allure.step("Ожидаем 400, InvalidForm"):
        assert resp.status_code == 400
