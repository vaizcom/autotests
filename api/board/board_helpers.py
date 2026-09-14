import random
import time

from api.board.board_endpoints import get_board_endpoint


def get_random_type_id(client, board_id, space_id):
    """Получение случайного _id из typesList борды."""
    response = client.post(**get_board_endpoint(board_id=board_id, space_id=space_id))
    response.raise_for_status()

    board_data = response.json().get("payload", {}).get("board", {})
    types_list = board_data.get("typesList", [])

    assert types_list, "Ошибка: typesList пуст или не существует."

    random_type = random.choice(types_list)
    return random_type["_id"]


def get_two_random_types(client, board_id, space_id):
    """
    Получение двух разных типов из typesList борды.
    Возвращает list of tuples [(type_id, type_name), (type_id, type_name)].
    """
    response = client.post(**get_board_endpoint(board_id=board_id, space_id=space_id))
    response.raise_for_status()

    board_data = response.json().get("payload", {}).get("board", {})
    types_list = board_data.get("typesList", [])

    assert len(types_list) >= 2, f"Нужно минимум 2 типа на борде, найдено: {len(types_list)}"

    two = random.sample(types_list, 2)
    return [(t["_id"], t["label"]) for t in two]


def get_random_group_id(client, board_id, space_id):
    """Получение случайного _id группы из списка groups борды."""
    response = client.post(**get_board_endpoint(board_id=board_id, space_id=space_id))
    response.raise_for_status()

    board_data = response.json().get("payload", {}).get("board", {})
    groups = board_data.get("groups", [])

    assert groups, "Ошибка: groups пуст или не существует."

    random_group = random.choice(groups)
    return random_group["_id"]


def wait_group_empty(client, board_id, space_id, group_id, timeout=10, poll_interval=0.5):
    """Ожидает, пока группа не станет пустой, либо истекает timeout (сек)"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        board = client.post(**get_board_endpoint(board_id, space_id)).json()["payload"]["board"]
        tasks = board["taskOrderByGroups"].get(group_id, [])
        if not tasks:
            return
        time.sleep(poll_interval)
    raise AssertionError(f"Группа {group_id} осталась не пустой: {tasks}")
