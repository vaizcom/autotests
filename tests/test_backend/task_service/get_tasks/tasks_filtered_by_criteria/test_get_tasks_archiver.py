import allure
import pytest
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint
from test_backend.data.endpoints.archive.archive_task_endpoint import archive_task_endpoint
from test_backend.task_service.utils import get_member_profile

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.title("GetTasks archiver: фильтр по archiver")
@pytest.mark.parametrize(
    'client_fixture, expected_status, expected_name_prefix',
    [
        ('owner_client', 200, 'owner'),
        ('manager_client', 200, 'manager'),
        ('member_client', 200, 'member'),
        ('guest_client', 403, 'guest'),
    ],
    ids=['archiver: owner' , 'archiver: manager', 'archiver: member', 'archiver: guest'],
)
def test_get_tasks_filter_by_archiver(request, manager_client, client_fixture, main_space, expected_status, make_task_in_main, expected_name_prefix, main_board):
    """
    Тест проверяет функциональность фильтрации задач по ID архиватора для различных ролей.
        Шаги:
    1. Создаем задачу оунером,
    2. Аархивируем от имени пользователя с определенной ролью
    3. Проверяем, что заархивированная задача корректно отображается при фильтрации по ID архиватора."
    """
    allure.dynamic.title(
        f"GetTasks: фильтр по archiver: archiver={expected_name_prefix}_id, ожидаемый статус={expected_status}")
    client = request.getfixturevalue(client_fixture)
    archiver_id = get_member_profile(space_id=main_space,
                                          client=client)  # архиватором будет тот же пользователь этой роли
    with allure.step("Подготовка данных: Созаем задачу (Owner)"):

        created_task = make_task_in_main({
            "name": "GetTasks: фильтр по archiver",
        })
        task_id = created_task.get("_id")

    with allure.step(f"Архивирование задачи в роли {expected_name_prefix} и проверка статуса {expected_status}"):
        arch_resp = client.post(**archive_task_endpoint(task_id=task_id, space_id=main_space))
        assert arch_resp.status_code == expected_status, (
            f"Не удалось удалить задачу {task_id}: {arch_resp.status_code} {arch_resp.text}"
        )

    with allure.step(f"Вызвать GetTasks с фильтром archiver: {expected_name_prefix}_id"):
        resp = manager_client.post(
            **get_tasks_endpoint(space_id=main_space, archiver=archiver_id))

    with allure.step("Проверить статус ответа GetTasks"):
        if expected_status == 200:  # Ожидалось успешное архивирование и поиск задачи
            assert resp.status_code == 200, \
                f"Ожидался статус 200 для GetTasks, но получен {resp.status_code} {resp.text} при поиске заархивированной задачи."
            with allure.step("Проверить наличие и корректность заархивированной задачи (archiver_id)"):
                tasks = resp.json().get("payload", {}).get("tasks", [])
                found_archived_task = next((task for task in tasks if task.get("_id") == task_id), None)
                assert found_archived_task is not None, f"Заархивированная задача с ID {task_id} не найдена при фильтрации по archiver."
                assert found_archived_task.get("archiver") == archiver_id, \
                    f"Неверный archiverId для задачи {task_id}. Ожидалось {archiver_id}, получено {found_archived_task.get('archiver')}."
        elif expected_status == 403:  # Ожидалось, что архивирование не произойдет (для guest_client)
            # В этом случае GetTasks с фильтром по archiver_id должен вернуть 200 OK, но список задач должен быть пустым.
            assert resp.status_code == 200, \
                f"При неуспешном архивировании (статус {expected_status}) GetTasks с фильтром по archiver={archiver_id} вернул статус {resp.status_code} {resp.text}. Ожидался 200."
            with allure.step("Проверить отсутствие задач (пустой список), т.к. архивирование в роли guest запрещено "):
                tasks = resp.json().get("payload", {}).get("tasks", [])
                found_archived_task = next((task for task in tasks if task.get("_id") == task_id), None)
                assert found_archived_task is None, \
                    f"Задача с ID {task_id} найдена при фильтрации по archiver={archiver_id}, хотя архивирование не удалось."
        else:  # Любой другой неожиданный expected_status для архивирования
            pytest.fail(f"Неожиданный ожидаемый статус {expected_status} для архивирования задачи.")