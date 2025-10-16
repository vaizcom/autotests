import random
import allure
import pytest

from test_backend.task.utils import get_client
from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.task.utils import get_random_group_id

pytestmark = [pytest.mark.backend]

@allure.title("Создание задачи на доске и проверка: группа, индекс и уникальность размещения")
def test_create_task_and_verify_on_board(request, create_task_in_main, main_space, main_board):
    """
    Тест создает задачу с указанными бордой, группой и индексом=0, и проверяет:
      - корректность задачи,
      - что задача только в одной группе, нет дублей, верный индекс=0.
      - random client_fixture
    """
    random_client = random.choice(["owner_client", "manager_client", "member_client"])
    client = get_client(request, random_client)
    random_group_id = get_random_group_id(client, main_board, main_space)
    task_index = 0

    with allure.step(f"Создаем задачу от случайного пользователя: {random_client}"):
        task = create_task_in_main(
            client_fixture=random_client,
            group=random_group_id,
            index=task_index
        )
        task_id = task["_id"]

    with allure.step("Проверяем созданную задачу"):
        assert task["board"] == main_board, "Ошибка: неверная борда задачи"
        assert task["group"] == random_group_id, "Ошибка: неверная группа задачи"

    with allure.step("Получаем данные борды через get_board_endpoint"):
        response = client.post(**get_board_endpoint(board_id=main_board, space_id=main_space))
        response.raise_for_status()
        board_data = response.json()["payload"]["board"]

    with allure.step("Проверяем 'taskOrderByGroups'"):
        assert isinstance(board_data["taskOrderByGroups"], dict), "'taskOrderByGroups' должен быть dict"
        for group_id_key, ids_list in board_data["taskOrderByGroups"].items():
            assert isinstance(ids_list, list), f"'taskOrderByGroups[{group_id_key}]' должен быть списком"
            for task_id_item in ids_list:
                assert isinstance(task_id_item, str), f"task_id должен быть строкой, найдено: {task_id_item}"

    with allure.step("Проверяем, что задача есть только в одной группе и нет дублей"):
        found_in_groups = []
        for group_id_key, ids_list in board_data["taskOrderByGroups"].items():
            if task_id in ids_list:
                found_in_groups.append(group_id_key)
        assert found_in_groups == [random_group_id], (
            f"Ошибка: задача присутствует в других группах: {found_in_groups}, ожидалась только {random_group_id}"
        )
        ids_in_group = board_data["taskOrderByGroups"].get(random_group_id, [])
        assert ids_in_group.count(task_id) == 1, (
            f"Ошибка: задача {task_id} содержится в группе {random_group_id} более одного раза: {ids_in_group}"
        )

    with allure.step("Проверяем корректность индекса задачи в группе"):
        ids_in_group = board_data["taskOrderByGroups"].get(random_group_id, [])
        position_in_group = ids_in_group.index(task_id) if task_id in ids_in_group else None
        assert position_in_group == task_index, (
            f"Ошибка: индекс задачи в группе {random_group_id} = {position_in_group}, ожидалось {task_index}. "
            f"taskOrderByGroups[{random_group_id}] = {ids_in_group}"
        )