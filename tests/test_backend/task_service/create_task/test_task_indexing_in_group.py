import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint
from test_backend.task_service.utils import delete_all_group_tasks
from tests.test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Create Task")
@allure.title("Create Task: Проверка что index соответствует ожидаемой позиции задачи в колонке")
@pytest.mark.parametrize(
    "initial_tasks, create_index, expected_position, title",
    [
        (0, None, 0, "Пустая группа, индекс не указан"),
        (0, 0, 0, "Пустая группа, индекс=0"),
        (0, 10, 0, "Пустая группа, индекс=10"),
        (10, 2, 2, "Группа из 10 тасок, индекс=2"),
        (10, 999, 10, "Группа из 10 тасок, индекс=999"),
        (10, 0, 0, "Группа из 10 тасок, индекс=0"),
        (10, 10, 10, "Группа из 10 тасок, индекс=10"),
        (10, 9, 9, "Группа из 10 тасок, индекс=9"),
        (10, None, 10, "Группа из 10 тасок, индекс не указан")
    ],
    ids=[
        "empty_group_no_index",
        "empty_group_index_0",
        "empty_group_index_10",
        "ten_tasks_index_2",
        "ten_tasks_index_999",
        "ten_tasks_index_0",
        "ten_tasks_index_10",
        "ten_tasks_index_9",
        "ten_tasks_index_none"
    ]
)
def test_task_indexing_in_group(
        request, temp_space, temp_board, initial_tasks, create_index, expected_position, title, main_client
):
    """
    Тест проверяет корректность позиционирования задач при создании новой задачи
    в гарантированно пустой группе на новой временной доске.
    """
    allure.dynamic.title(f"Проверка index -> ожидаемая позиция задачи в колонке | {title}")
    with allure.step("Получить ID первой группы на новой доске"):
        resp = main_client.post(**get_board_endpoint(temp_board, temp_space))
        group_id = resp.json()["payload"]["board"]["groups"][0]["_id"]

    with allure.step("Очистить дефолтные задачи с новой доски (если они есть)"):
        delete_all_group_tasks(main_client, temp_board, temp_space, group_id)

    with allure.step(f"Подготовка: Добавление {initial_tasks} стартовых задач в группу"):
        for i in range(initial_tasks):
            main_client.post(
                **create_task_endpoint(
                    space_id=temp_space,
                    board=temp_board,
                    group=group_id,
                    index=i,
                    name=f"Initial Task #{i}"
                )
            )

        with allure.step(f"Действие: Создать новую целевую задачу: {title}"):
            resp_target = main_client.post(
                **create_task_endpoint(
                    space_id=temp_space,
                    board=temp_board,
                    group=group_id,
                    name="Target Task!!!!",
                    index=create_index
                )
            )
            assert resp_target.status_code == 200, f"Ошибка создания задачи: {resp_target.text}"
            target_task_id = resp_target.json()["payload"]["task"]["_id"]

        with allure.step("Проверка: Запросить список задач группы и проверить порядок"):
            board = main_client.post(**get_board_endpoint(temp_board, temp_space)).json()["payload"]["board"]

        task_ids = board["taskOrderByGroups"].get(group_id, [])

        assert target_task_id in task_ids, "Созданная задача отсутствует в списке taskOrderByGroups"

        actual_position = task_ids.index(target_task_id)
        assert actual_position == expected_position, (
            f"Задача в позиции {actual_position}, ожидалось {expected_position}. \nСписок: {task_ids}"
        )

        expected_count = initial_tasks + 1
        assert len(task_ids) == expected_count, (
            f"Ожидалось задач: {expected_count}, получено: {len(task_ids)}.\nСписок: {task_ids}"
        )