import pytest
import allure
import time
from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint
from test_backend.task.utils import wait_group_empty, safe_delete_all_tasks_in_group, \
    delete_all_group_tasks

pytestmark = [pytest.mark.backend]

@pytest.mark.parametrize(
    "initial_tasks, create_index, expected_position, title",
    [
        (0, None, 0, "Пустая группа, индекс не указан"),
        (0, 0, 0, "Пустая группа, индекс=0"),
        (0, 10, 0, "Пустая группа, индекс=10"),
        (10, 2, 2, "Группа из 10 тасок, индекс=2"),
        (10, 999, 10, "Группа из 10 тасок, индекс=999"),
        (10, 0, 0, "Группа из 10 тасок, индекс=0"),
        (10, 10,10, "Группа из 10 тасок, индекс=10"),
        (10,9,9, "Группа из 10 тасок, индекс=9")
    ],
    ids=[
        "empty_group_no_index",
        "empty_group_index_0",
        "empty_group_index_10",
        "ten_tasks_index_2",
        "ten_tasks_index_999",
        "ten_tasks_index_0",
        "ten_tasks_index_10",
        "ten_tasks_index_9"
    ]
)
def test_task_indexing_in_group(
    request, create_task_in_main, main_space, main_board, initial_tasks, create_index, expected_position, title,
):
    """
    Тест проверяет корректность позиционирования задач при создании новой задачи в группе на доске (board).
    """

    with allure.step("Получить ID первой группы на доске"):
        client = request.getfixturevalue("owner_client")
        resp = client.post(**get_board_endpoint(main_board, main_space))
        group_id = resp.json()["payload"]["board"]["groups"][0]["_id"]

    with allure.step("Очистить все задачи в выбранной группе"):
        delete_all_group_tasks(client, main_board, main_space, group_id)

    try:
        with allure.step("Убедиться, что группа действительно пуста"):
            for try_num in range(5):
                board = client.post(**get_board_endpoint(main_board, main_space)).json()["payload"]["board"]
                task_ids = board["taskOrderByGroups"].get(group_id, [])
                if not task_ids:
                    break
                time.sleep(1)
            assert not task_ids, f"Группа не пуста после очистки! Остались: {task_ids}"

        with allure.step("Добавить стартовые задачи в группу (если требуется по сценарию)"):
            for i in range(initial_tasks):
                create_task_in_main(
                    client_fixture="owner_client",
                    group=group_id,
                    index=i,
                    name=f"Initial Task #{i}"
                )

        with allure.step(f"Создать новую тестовую задачу: {title}"):
            params = {
                "client_fixture": "owner_client",
                "group": group_id,
                "name": "Target Task!!!!",
                "index": create_index,
            }
            target_task = create_task_in_main(**params)
            target_task_id = target_task["_id"]

        with allure.step("Запросить список задач группы и проверить корректность порядка"):
            board = client.post(**get_board_endpoint(main_board, main_space)).json()["payload"]["board"]
            task_ids = board["taskOrderByGroups"][group_id]
            assert target_task_id in task_ids, "Задача должна быть в списке задач группы"
            actual_position = task_ids.index(target_task_id)
            assert actual_position == expected_position, (
                f"Задача в позиции {actual_position}, ожидалось {expected_position}. Список: {task_ids}"
            )

        # Проверка количества задач: всегда должно быть initial_tasks + 1
            expected_count = initial_tasks + 1
            assert len(task_ids) == expected_count, (
                f"Ожидалось задач: {expected_count}, получено: {len(task_ids)}.\n"
                f"Список задач: {task_ids}"
            )
            if expected_count == 1:
                assert actual_position == 0, "Если задача единственная, её индекс должен быть 0"
                assert task_ids == [target_task_id], (
                    f"Единственная задача должна быть именно той, что создана сейчас. Получено: {task_ids}"
                )
    finally:
        with allure.step("Финальная очистка группы после завершения теста"):
            safe_delete_all_tasks_in_group(client, main_board, main_space, group_id)
            wait_group_empty(client, main_board, main_space, group_id)



@pytest.mark.parametrize("negative_index", [-1, -10])
def test_create_task_with_negative_index_returns_error(
    request, main_space, main_board, negative_index
):
    """
    Негативный тест: создание задачи с отрицательным индексом должно возвращать ошибку по полю index.
    """
    client = request.getfixturevalue("owner_client")
    payload = create_task_endpoint(
        space_id=main_space,
        board=main_board,
        name="Test negative index",
        index=negative_index,
    )
    with allure.step(f"Пробуем создать задачу с index={negative_index}"):
        response = client.post(**payload)

    with allure.step("Проверяем структуру и содержание ошибки"):
        assert response.status_code == 400, f"Ожидался статус 400, получено {response.status_code}, ответ: {response.text}"
        body = response.json()
        assert body.get("error"), "В ответе нет поля 'error'"
        error = body["error"]
        assert error.get("code") == "InvalidForm", f"Ожидался code=InvalidForm, получено: {error.get('code')}"
        fields = error.get("fields")
        assert fields and isinstance(fields, list), "Поле 'fields' отсутствует или не является списком"
        index_field = next((f for f in fields if f.get("name") == "index"), None)
        assert index_field is not None, "В ошибке нет информации по полю 'index'"
        codes = index_field.get("codes", [])
        assert any("must not be less than 0" in code for code in codes), (
            f"Ожидалось сообщение о недопустимом отрицательном индексе, получили: {codes}"
        )