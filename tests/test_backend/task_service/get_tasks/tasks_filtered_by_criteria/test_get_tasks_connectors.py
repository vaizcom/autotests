import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("tasks_filtered_by_criteria")
@allure.title("Проверка фильтрации задач по rightConnectors")
def test_get_tasks_filter_by_right_connectors(owner_client, main_space, board_with_tasks):
    """
    Подготовлены заренее таски для проверки на борде(board_with_tasks)

    Проверяет, что при запросе задач с фильтром по rightConnectors
    в ответе содержатся только те задачи, у которых есть хотя бы один
    из указанных rightConnectors ID.
    """
    target_right_connector_id = "6936aa59be4152d4a15dc510"
    target_task_id = "6936aa02be4152d4a15dc357"

    with allure.step("Выполнить запрос с фильтрацией по rightConnectors"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            rightConnectors=[target_right_connector_id],
        ))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200, resp.text

    with allure.step("Извлечь задачи и проверить их наличие"):
        tasks = resp.json()["payload"]["tasks"]
        assert tasks, "Ожидаются задачи в ответе при фильтрации по rightConnectors"

    with allure.step("Проверить, что задача с ID присутствует в ответе"):
        assert any(task["_id"] == target_task_id for task in tasks), \
            "Задача с ID не найдена в отфильтрованном списке задач по rightConnectors."

    with allure.step("Проверить, что все задачи содержат указанный rightConnector ID"):
        for task in tasks:
            # Убеждаемся, что поле 'rightConnectors' существует и является списком
            assert "rightConnectors" in task and isinstance(task["rightConnectors"], list), \
                f"Задача {task.get('_id', 'N/A')} не содержит или содержит неверный тип 'rightConnectors'."

            # Проверяем, что target_right_connector_id присутствует в списке rightConnectors задачи
            assert target_right_connector_id in task["rightConnectors"], \
                f"Задача {task.get('_id', 'N/A')} не содержит rightConnector ID '{target_right_connector_id}'."

    allure.attach(
        f"Количество задач с rightConnector ID '{target_right_connector_id}': {len(tasks)}",
        name="Результат фильтрации по rightConnectors",
        attachment_type=allure.attachment_type.TEXT
    )


@allure.parent_suite("tasks_filtered_by_criteria")
@allure.title("Проверка фильтрации задач по leftConnectors")
def test_get_tasks_filter_by_left_connectors(owner_client, main_space, board_with_tasks):
    """
    Подготовлены заренее таски для проверки на борде(board_with_tasks)

    Проверяет, что при запросе задач с фильтром по leftConnectors
    в ответе содержатся только те задачи, у которых есть хотя бы один
    из указанных leftConnectors ID.
    """
    target_left_connector_id = '6936aa4ebe4152d4a15dc435'
    target_task_id = "6936aa02be4152d4a15dc357"

    with allure.step("Выполнить запрос с фильтрацией по leftConnectors"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            leftConnectors=[target_left_connector_id]
        ))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200, resp.text

    with allure.step("Извлечь задачи и проверить их наличие"):
        tasks = resp.json()["payload"]["tasks"]
        assert tasks, "Ожидаются задачи в ответе при фильтрации по leftConnectors"

    with allure.step("Проверить, что задача с ID присутствует в ответе"):
        assert any(task["_id"] == target_task_id for task in tasks), \
            "Задача с ID не найдена в отфильтрованном списке задач по rightConnectors."

    with allure.step("Проверить, что все задачи содержат указанный leftConnector ID"):
        for task in tasks:
            # Убеждаемся, что поле 'leftConnectors' существует и является списком
            assert "leftConnectors" in task and isinstance(task["leftConnectors"], list), \
                f"Задача {task.get('_id', 'N/A')} не содержит или содержит неверный тип 'leftConnectors'."

            # Проверяем, что target_left_connector_id присутствует в списке leftConnectors задачи
            assert target_left_connector_id in task["leftConnectors"], \
                f"Задача {task.get('_id', 'N/A')} не содержит leftConnector ID '{target_left_connector_id}'."

    allure.attach(
        f"Количество задач с leftConnector ID '{target_left_connector_id}': {len(tasks)}",
        name="Результат фильтрации по leftConnectors",
        attachment_type=allure.attachment_type.TEXT
    )