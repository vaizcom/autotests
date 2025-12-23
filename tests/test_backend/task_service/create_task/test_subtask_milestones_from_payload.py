import allure
import pytest
from test_backend.task_service.utils import get_subtask_ms_1, get_subtask_ms_2, delete_task_with_retry, \
    get_parent_ms_1, get_parent_ms_2

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Task Service")
@allure.suite("Create Task")
@allure.title("Create Task Новая логика: Milestone у сабтаска берется из payload, а не наследуются от родителя")
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
    with allure.step("Получаем IDs milestons для родителя"):
        parent_ms_id_1 = get_parent_ms_1(owner_client, main_space, main_board)
        parent_ms_id_2 = get_parent_ms_2(owner_client, main_space, main_board)


    with allure.step("Создаём родительскую задачу"):
        parent = create_task_in_main("owner_client", milestones=[parent_ms_id_1, parent_ms_id_2])
        parent_task = parent["_id"]

    with allure.step("Получаем ID milestone для сабтаска"):
        subtask_ms_id = get_subtask_ms_1(owner_client, main_space, main_board)

    with allure.step("Создаём сабтаск с milestone"):
        subtask = create_task_in_main("owner_client", parent_task=parent_task, milestones=[subtask_ms_id])

    try:
        with allure.step("Проверяем, что у сабтаска создана с собственным milestone(milestone берется из payload)"):
            expected_subtask_ms_id = [subtask_ms_id]
            assert subtask["milestones"] == [subtask_ms_id], (
                f"Ожидались milestones {expected_subtask_ms_id}, получили {subtask.get('milestones')}"
            )
        with allure.step("Проверяем, что у родительской таски корректные milestones(milestone берется из payload)"):
            expected_parents_ms_id = [parent_ms_id_1, parent_ms_id_2]
            assert parent["milestones"] == expected_parents_ms_id, (
                f"Ожидались milestones {expected_parents_ms_id}, получили {parent.get('milestones')}"
            )
    finally:
        with allure.step("Удаляем сабтаск и родительскую задачу после теста"):
            delete_task_with_retry(owner_client, subtask["_id"], main_space)
            delete_task_with_retry(owner_client, parent["_id"], main_space)


@allure.parent_suite("Task Service")
@allure.suite("Create Task")
@allure.title("Create Task: Если поле milestone у сабтаска пустое, оно также не наследует milestone от родителя.")
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
    with allure.step("Получаем ID milestone для родителя"):
        parent_ms_id = get_parent_ms_1(owner_client, main_space, main_board)

    with allure.step("Создаём родительскую задачу"):
        parent = create_task_in_main("owner_client", milestones=[parent_ms_id])
        parent_task = parent["_id"]

    with allure.step("Создаём сабтаск без milestone"):
        subtask = create_task_in_main("owner_client", parent_task=parent_task)

    try:
        with allure.step("Проверяем, что у сабтаска milestone отсутствует(не наследуется от родителя)"):
            expected_ms_id = []
            assert subtask["milestones"] == expected_ms_id, (
                f"Ожидались milestones {expected_ms_id}, получили {subtask.get('milestones')}"
            )
        with allure.step("Проверяем, что у родительской таски корректные milestones(milestone берется из payload)"):
            expected_parents_ms_id = [parent_ms_id]
            assert parent["milestones"] == expected_parents_ms_id, (
                f"Ожидались milestones {expected_parents_ms_id}, получили {parent.get('milestones')}"
            )
    finally:
        with allure.step("Удаляем сабтаск и родительскую задачу после теста"):
            delete_task_with_retry(owner_client, subtask["_id"], main_space)
            delete_task_with_retry(owner_client, parent["_id"], main_space)


@allure.parent_suite("Task Service")
@allure.suite("Create Task")
@allure.title("Create Task: Проверка создания нескольких сабтасков с разными milestone, также не наследует milestone родителя.")
def test_create_subtasks_with_various_milestones(
    create_task_in_main, owner_client, main_space, main_board
):
    """
    Создание сабтасков с разными milestone.

    Шаги:
    1. Получить ID milestone для родителя (A), сабтасков (B и C).
    2. Создать родительскую задачу.
    3. Сформировать payload с несколькими сабтасками (разные milestone, пустой milestone).
    4. Создать сабтаски.
    5. Проверить, что у каждого сабтаска свой milestone/отсутствие milestone.
    6. Удалить все созданные сабтаски и родителя.
    """
    with allure.step("Получаем ID milestone для родителя (A)"):
        parent_ms_id = get_parent_ms_1(owner_client, main_space, main_board)
    with allure.step("Получаем ID milestone для сабтаска 1 (B)"):
        ms_1 = get_subtask_ms_1(owner_client, main_space, main_board)
    with allure.step("Получаем ID milestone для сабтаска 2 (C)"):
        ms_2 = get_subtask_ms_2(owner_client, main_space, main_board)
    with allure.step("Создаём родительскую задачу"):
        parent = create_task_in_main("owner_client", milestones=[parent_ms_id])
        parent_id = parent["_id"]

    # Создаём сабтаски по отдельности
    with allure.step("Создаём Subtask #1 с milestone B"):
        subtask1 = create_task_in_main("owner_client", parent_task=parent_id, milestones=[ms_1], name="Subtask #1")
    with allure.step("Создаём Subtask #2 с milestone C"):
        subtask2 = create_task_in_main("owner_client", parent_task=parent_id, milestones=[ms_2], name="Subtask #2")
    with allure.step("Создаём Subtask #3 без milestone"):
        subtask3 = create_task_in_main("owner_client", parent_task=parent_id, milestones=[], name="Subtask #3")

    subtasks = [subtask1, subtask2, subtask3]

    try:
        with allure.step("Проверяем milestones у всех созданных сабтасков"):
            assert subtask1["milestones"] == [ms_1], f"Subtask #1: ожидался milestone {ms_1}"
            assert subtask2["milestones"] == [ms_2], f"Subtask #2: ожидался milestone {ms_2}"
            assert subtask3["milestones"] == [], "Subtask #3: ожидался пустой milestone"

        with allure.step("Проверяем, что у родительской таски корректные milestones(milestone берется из payload)"):
            expected_parents_ms_id = [parent_ms_id]
            assert parent["milestones"] == expected_parents_ms_id, (
                f"Ожидались milestones {expected_parents_ms_id}, получили {parent.get('milestones')}"
            )
    finally:
        with allure.step("Удаляем все сабтаски и родительскую задачу после теста"):
            for subtask in subtasks:
                delete_task_with_retry(owner_client, subtask["_id"], main_space)
            delete_task_with_retry(owner_client, parent_id, main_space)