import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.title("GetTasks: Проверка доступа к задачам для всех ролей (с фильтрацией по борде)")
@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200)
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_get_tasks_filtered_by_board_by_role(request, client_fixture, expected_status, board_with_tasks, main_space):
    """
    Проверка фильтрации по конкретной борде для всех ролей:
    - роли с доступом: HTTP 200 и все задачи принадлежат указанной борде;
    """
    client = request.getfixturevalue(client_fixture)
    role_name = client_fixture.replace('_client', '').capitalize()
    allure.dynamic.title(f"Доступ к таскам с фильтрацией по board под ролью {role_name} (HTTP {expected_status})")

    with allure.step(f"{client_fixture}: вызвать GetTasks с фильтром board"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_tasks))

    with allure.step(f"Проверить HTTP {expected_status}"):
        assert resp.status_code == expected_status

    with allure.step("Проверить payload и фильтрацию по board"):
        payload = resp.json().get("payload", {})
        assert "tasks" in payload and isinstance(payload["tasks"], list)
        tasks = payload["tasks"]

        if not tasks:
            pytest.skip("Список задач пуст — нечего валидировать по фильтру борды")

        for task in tasks[20:]:
            assert task.get("board") == board_with_tasks, (
                f"Задача {task.get('_id', 'unknown')} принадлежит другой board: {task.get('board')}"
            )

        with allure.step("Дополнительная проверка: отсутствие задач из соседней борды (этого же проекта)"):
            another_board_id = "6866309d85fb8d104544a637"
            for task in tasks[50:]:
                assert task.get("board") != another_board_id, (
                    f"Найдена задача {task.get('_id', 'unknown')} из чужой борды {another_board_id}"
                )


@allure.title("GetTasks: Проверка что список задач пустой для пользователей которые не имеют доступ к борде")
@pytest.mark.parametrize(
    'client_fixture',
    ['client_with_access_only_in_space', 'client_with_access_only_in_project'],
    ids=['no_access_to_project', 'no_access_to_board'],
)
def test_get_tasks_limited_access_filtered_by_board(request, client_fixture, board_with_tasks, main_space):
    """
        Проверка что список задач пустой для пользователей которые не имеют доступ к борде

        Проверяет, что пользователи без доступа к проекту или доске получают пустой список задач,
        но при этом запрос выполняется успешно (HTTP 200).
        """
    role_name = client_fixture.capitalize()
    allure.dynamic.title(f"Тестирование получения задач под ролью {role_name}")

    client = request.getfixturevalue(client_fixture)

    with allure.step(f"{client_fixture}: вызвать GetTasks с фильтром board"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_tasks))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Проверить что список задач пустой"):
        payload = resp.json().get("payload", {})
        assert "tasks" in payload and isinstance(payload["tasks"], list)
        assert len(payload["tasks"]) == 0, f"Ожидался пустой список задач для {client_fixture}"

@allure.title("Проверка что пользователь без доступа к спейсу не имеет доступ к задачам board")
def test_get_tasks_no_access_filtered_by_board(request, board_with_tasks, main_space):
    client = request.getfixturevalue('foreign_client')

    with allure.step("foreign_client: вызвать GetTasks"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_tasks))

    with allure.step("Проверить HTTP 400"):
        assert resp.status_code == 400