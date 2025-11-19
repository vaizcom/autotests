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
        ('guest_client', 200, 'guest')
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_get_tasks_filtered_by_creator(request, client_fixture, main_space, expected_status, expected_name_prefix, board_with_tasks_created_all_clients):
    allure.dynamic.title(
        f"GetTasks: фильтр по creator: клиент={expected_name_prefix}, ожидаемый статус={expected_status}")
    client = request.getfixturevalue(client_fixture)

    with allure.step(f"Подготовка данных для {expected_name_prefix}: получить профиль участника и определить его creator_id"):
        member_id = get_member_profile(space_id=main_space, client=client)

    with allure.step(f"{expected_name_prefix}: вызвать GetTasks с фильтром creator"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, creator=member_id, board=board_with_tasks_created_all_clients))

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
                    "Проверить что для guest_client список задач с фильтром creator пуст, т.к. он не может создавать задачи, только просматривать"):
                assert client_fixture == 'guest_client', (
                    f"Пустой список задач допустим только для guest_client, но текущий клиент: {client_fixture}"
                )