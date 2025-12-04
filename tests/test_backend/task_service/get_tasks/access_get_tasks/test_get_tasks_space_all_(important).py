import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.title("GetTasks: Проверка доступа к задачам спейса для всех ролей (без фильтраций)")
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
def test_get_tasks_by_role_in_second_space(request, client_fixture, expected_status, second_space, second_project, main_project):
    """
    Проверка доступа ко всем таскам в спейсе для всех ролей:
    - роли с доступом: HTTP 200 и все задачи принадлежат ТОЛЬКО указанному спейсу;

    TODO: после исправления бага добавить проверку, что заархивированные задачи не попадают в выборку
    (сейчас указан спейс в котором нет архивных тасок)
    """
    client = request.getfixturevalue(client_fixture)
    role_name = client_fixture.replace('_client', '').capitalize()
    allure.dynamic.title(f"Доступ к таскам спейса под ролью {role_name} (HTTP {expected_status})")

    with allure.step(f"{client_fixture}: вызвать GetTasks без фильтров"):
        resp = client.post(**get_tasks_endpoint(space_id=second_space))

    with allure.step(f"Проверить HTTP {expected_status}"):
        assert resp.status_code == expected_status

    with allure.step("Проверить payload"):
        payload = resp.json().get("payload", {})
        assert "tasks" in payload and isinstance(payload["tasks"], list)
        tasks = payload["tasks"]

    if not tasks:
        pytest.skip("Список задач пуст — нечего валидировать")

    # Жёсткая проверка: каждая задача должна принадлежать только second_project
    with allure.step("Проверить отсутствие задач из другого спейса)"):
        for task in tasks[:20]:
            assert "project" in task, f"У задачи {task.get('_id', 'unknown')} отсутствует поле project"
            assert task.get("project") == second_project, (
                f"Задача {task.get('_id', 'unknown')} принадлежит другому проекту: {task.get('project')}, "
                f"ожидался {second_project}"
                )


@allure.title("Проверка что пользователь без доступа к спейсу не имеет доступ к задачам")
def test_get_tasks_no_access(request, main_space):
    client = request.getfixturevalue('foreign_client')

    with allure.step("foreign_client: вызвать GetTasks"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space))

    with allure.step("Проверить HTTP 400"):
        assert resp.status_code == 400