import allure

from api.board.board_endpoints import get_board_endpoint
from api.milestone.milestone_helpers import get_parent_ms_1, get_subtask_ms_1, get_subtask_ms_2


def create_task(client, payload):
    """Helper function to create task."""
    return client.post(**payload)


def get_client(request, client_fixture):
    """Получение клиента из тестового фикстура."""
    return request.getfixturevalue(client_fixture)


def create_parent_and_subtasks(create_task_in_main, client_fixture, owner_client, main_space, main_board):
    """
    Создает родительскую задачу с milestone parent_ms_1,
    три подзадачи: первая с milestone subtask_ms_1,
    вторая с milestone subtask_ms_2, третья без milestone.
    Задачи распределяются по разным группам борды.

    Возвращает:
        ids (dict): словарь с ключами 'parent', 'subtask1', 'subtask2', 'subtask3' и их _id
        ms (dict): словарь с ID майлстоунов
    """
    parent_ms_1 = get_parent_ms_1(owner_client, main_space, main_board)
    subtask_ms_1 = get_subtask_ms_1(owner_client, main_space, main_board)
    subtask_ms_2 = get_subtask_ms_2(owner_client, main_space, main_board)

    ms = {
        "parent_ms_1": parent_ms_1,
        "subtask_ms_1": subtask_ms_1,
        "subtask_ms_2": subtask_ms_2
    }

    resp = owner_client.post(**get_board_endpoint(main_board, main_space))
    groups = resp.json()["payload"]["board"]["groups"]
    assert len(groups) >= 2, "На борде меньше 2 групп"
    group_a = groups[0]["_id"]
    group_b = groups[1]["_id"]

    created_tasks = []

    with allure.step('Создание родительской задачи с milestone parent_ms_1'):
        parent_task = create_task_in_main(
            client_fixture,
            name="Parent Task with milestone parent_ms_1",
            milestones=[parent_ms_1],
            group=group_a,
        )
        created_tasks.append(parent_task)
        parent_task_id = parent_task["_id"]

    with allure.step('Создание первой подзадачи с milestone subtask_ms_1'):
        subtask1 = create_task_in_main(
            client_fixture,
            name="Subtask 1 with milestone subtask_ms_1",
            milestones=[subtask_ms_1],
            parent_task=parent_task_id,
            group=group_b,
        )
        created_tasks.append(subtask1)
        subtask1_id = subtask1["_id"]

    with allure.step('Создание второй подзадачи с milestone subtask_ms_2'):
        subtask2 = create_task_in_main(
            client_fixture,
            name="Subtask 2 with milestone subtask_ms_2",
            milestones=[subtask_ms_2],
            parent_task=parent_task_id,
            group=group_a,
        )
        created_tasks.append(subtask2)
        subtask2_id = subtask2["_id"]

    with allure.step('Создание третьей подзадачи без milestone'):
        subtask3 = create_task_in_main(
            client_fixture,
            name="Subtask 3 without milestone",
            milestones=[],
            parent_task=parent_task_id,
            group=group_b,
        )
        created_tasks.append(subtask3)
        subtask3_id = subtask3["_id"]

    assert parent_task["group"] == group_a, \
        f"Parent: ожидалась группа {group_a}, получена {parent_task['group']}"
    assert subtask1["group"] == group_b, \
        f"Subtask1: ожидалась группа {group_b}, получена {subtask1['group']}"
    assert subtask2["group"] == group_a, \
        f"Subtask2: ожидалась группа {group_a}, получена {subtask2['group']}"
    assert subtask3["group"] == group_b, \
        f"Subtask3: ожидалась группа {group_b}, получена {subtask3['group']}"

    ids = {
        "parent": parent_task_id,
        "subtask1": subtask1_id,
        "subtask2": subtask2_id,
        "subtask3": subtask3_id,
    }

    return ids, ms
