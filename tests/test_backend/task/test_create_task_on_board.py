import allure

from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.task.utils import get_client


def test_create_task_and_verify_on_board(request, create_task_in_main, main_space, main_board):
    """
    Тест создает задачу с указанными бордой, группой и индексом, а затем проверяет корректность этой задачи на борде.
    """
    client_fixture = "owner_client"
    group_id = "6866731185fb8d104544e828"
    task_index = 5

    # Создание задачи
    with allure.step("Создаем задачу с указанными параметрами"):
        task = create_task_in_main(
            client_fixture=client_fixture,
            group=group_id,
            index=task_index
        )

    # Проверяем, что задача была успешно создана
    with allure.step("Проверяем созданную задачу"):
        assert task["board"] == main_board, "Ошибка: неверная борда задачи"
        assert task["group"] == group_id, "Ошибка: неверная группа задачи"
        assert task["index"] == task_index, "Ошибка: неверный индекс задачи"

    # Получение данных борды для проверки
    with allure.step("Получаем данные борды через get_board_endpoint"):
        client = get_client(request, client_fixture)
        response = client.post(**get_board_endpoint(board_id=main_board, space_id=main_space))
        response.raise_for_status()
        board_data = response.json()["payload"]["board"]

    # Проверяем, что задача отображается на борде с корректными данными
    with allure.step("Проверяем, что задача присутствует на борде с корректными данными"):
        found_task = next((t for t in board_data["tasks"] if t["_id"] == task["_id"]), None)
        assert found_task, "Ошибка: задача не найдена на борде"
        assert found_task["group"] == group_id, "Ошибка: задача находится в неверной группе на борде"
        assert found_task["index"] == task_index, "Ошибка: неверный индекс задачи на борде"