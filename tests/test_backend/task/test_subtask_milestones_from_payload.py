import pytest
from test_backend.task.utils import get_parent_ms, get_subtask_ms_1, get_subtask_ms_2, delete_task_with_retry

pytestmark = [pytest.mark.backend]

def test_subtask_milestone_with_own_milestone(
    create_task_in_main,
    owner_client,
    main_space,
    main_board,
):
    """
    Создание сабтаска с собственным milestone.
    Сабтаск отображает milestone B (из payload), а не наследует milestone A от родителя.
    """
    parent_ms_id = get_parent_ms(owner_client, main_space, main_board)
    parent = create_task_in_main("owner_client", milestones=[parent_ms_id])
    parent_task = parent["_id"]

    subtask_ms_id = get_subtask_ms_1(owner_client, main_space, main_board)
    subtask = create_task_in_main("owner_client", parent_task=parent_task, milestones=[subtask_ms_id])

    try:
        expected_ms_id = [subtask_ms_id]
        assert subtask["milestones"] == expected_ms_id, (
            f"Ожидались milestones {expected_ms_id}, получили {subtask.get('milestones')}"
        )
    finally:
        # Удаляем сабтаск и родительскую задачу
        delete_task_with_retry(owner_client, subtask["_id"], main_space)
        delete_task_with_retry(owner_client, parent["_id"], main_space)


def test_subtask_milestone_without_own_milestone(
    create_task_in_main,
    owner_client,
    main_space,
    main_board,
):
    """
    Создание сабтаска без milestone в payload.
    Сабтаск не наследует milestone A автоматически у родителя.
    Поле milestone у сабтаска пустое.
    После теста задачи удаляются.
    """
    parent_ms_id = get_parent_ms(owner_client, main_space, main_board)
    parent = create_task_in_main("owner_client", milestones=[parent_ms_id])
    parent_task = parent["_id"]

    subtask = create_task_in_main("owner_client", parent_task=parent_task)
    try:
        expected_ms_id = []
        assert subtask["milestones"] == expected_ms_id, (
            f"Ожидались milestones {expected_ms_id}, получили {subtask.get('milestones')}"
        )
    finally:
        delete_task_with_retry(owner_client, subtask["_id"], main_space)
        delete_task_with_retry(owner_client, parent["_id"], main_space)


@pytest.mark.skip("Требуется реализовать редактирование сабтаска через API")
def test_edit_subtask_milestone(create_task_in_main, edit_task, owner_client, main_space, main_board):
    """
    Кейс 3: редактирование milestone у сабтаска.
    """
    parent_ms_id = get_parent_ms(owner_client, main_space, main_board)
    subtask_ms_id = get_subtask_ms_1(owner_client, main_space, main_board)
    new_subtask_ms_id = get_subtask_ms_2(owner_client, main_space, main_board)

    parent = create_task_in_main("owner_client", milestones=[parent_ms_id])
    subtask = create_task_in_main("owner_client", parent_task=parent["id"], milestones=[subtask_ms_id])

    # Меняем milestone сабтаска на 'C'
    subtask_edited = edit_task("owner_client", task_id=subtask["id"], milestones=[new_subtask_ms_id])

    assert subtask_edited["milestones"] == [new_subtask_ms_id]
    assert parent["milestones"] == [parent_ms_id]

@pytest.mark.skip("Требуется реализовать update для родителя через API")
def test_change_parent_milestone_does_not_update_subtask(create_task_in_main, edit_task, owner_client, main_space, main_board):
    """
    Кейс 4: изменение milestone у родителя не влияет на сабтаск.
    """
    parent_ms_id = get_parent_ms(owner_client, main_space, main_board)
    subtask_ms_id = get_subtask_ms_1(owner_client, main_space, main_board)
    new_parent_ms_id = get_subtask_ms_2(owner_client, main_space, main_board)

    parent = create_task_in_main("owner_client", milestones=[parent_ms_id])
    subtask = create_task_in_main("owner_client", parent_task=parent["id"], milestones=[subtask_ms_id])

    # Меняем milestone у родителя на 'C'
    parent_edited = edit_task("owner_client", task_id=parent["id"], milestones=[new_parent_ms_id])
    # milestone у сабтаска не должен измениться
    assert subtask["milestones"] == [subtask_ms_id]

@pytest.mark.skip("Требуется реализовать массовое создание сабтасков через API")
def test_bulk_create_subtasks_with_various_milestones(create_task_in_main, bulk_create_subtasks, owner_client, main_space, main_board):
    """
    Кейс 5: массовое создание сабтасков с разными milestone.
    """
    parent_ms_id = get_parent_ms(owner_client, main_space, main_board)
    ms_b = get_subtask_ms_1(owner_client, main_space, main_board)
    ms_c = get_subtask_ms_2(owner_client, main_space, main_board)
    parent = create_task_in_main("owner_client", milestones=[parent_ms_id])
    # Формируем payload для bulk
    subtasks_payload = [
        {"parent_task": parent["id"], "milestones": [ms_b], "name": "Subtask #1"},
        {"parent_task": parent["id"], "milestones": [ms_c], "name": "Subtask #2"},
        {"parent_task": parent["id"], "milestones": [], "name": "Subtask #3"},
    ]
    subtasks = bulk_create_subtasks("owner_client", subtasks_payload)
    assert subtasks[0]["milestones"] == [ms_b]
    assert subtasks[1]["milestones"] == [ms_c]
    assert subtasks[2]["milestones"] == []

@pytest.mark.skip("UI тест: реализуй с помощью инструмента для автотестов фронта")
def test_subtask_milestones_ui(ui_open_task_list, owner_client, main_space, main_board):
    """
    Кейс 6: проверка отображения milestone в UI.
    """
    ms_b = get_subtask_ms_1(owner_client, main_space, main_board)
    ms_c = get_subtask_ms_2(owner_client, main_space, main_board)
    parent_id, ui_subtasks = ui_open_task_list()
    assert ui_subtasks[0].milestones == [ms_b]
    assert ui_subtasks[1].milestones == [ms_c]
    assert not ui_subtasks[2].milestones  # milestone пустой