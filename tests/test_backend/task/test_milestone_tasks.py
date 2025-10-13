
import allure
import pytest

from test_backend.task.utils import delete_task_with_retry, get_milestone_tasks, get_parent_ms_1, get_subtask_ms_1, \
    get_subtask_ms_2

pytestmark = [pytest.mark.backend]

@allure.story('Проверка задач с разными milestone, включая parent и subtasks')
def test_tasks_visibility_in_correct_milestones(create_task_in_main, owner_client, main_space, main_board):
    """
    Создаём родительскую задачу с milestone parent_ms_1,
    затем три подзадачи:
    - первая с milestone subtask_ms_1
    - вторая с milestone subtask_ms_2
    - третья без milestone
    Проверяем, что все задачи корректно видны в соответствующих milestones.
    """
    parent_ms_1 = get_parent_ms_1(owner_client, main_space, main_board)
    subtask_ms_1 = get_subtask_ms_1(owner_client, main_space, main_board)
    subtask_ms_2 = get_subtask_ms_2(owner_client, main_space, main_board)

    created_tasks = []

    try:
        with allure.step('Создание родительской задачи с milestone parent_ms_1'):
            parent_task = create_task_in_main(
                "owner_client",
                name="Parent Task with milestone parent_ms_1",
                milestones=[parent_ms_1],
            )
            created_tasks.append(parent_task)
            parent_task_id = parent_task["_id"]

        with allure.step('Создание первой подзадачи с milestone subtask_ms_1'):
            subtask1 = create_task_in_main(
                "owner_client",
                name="Subtask 1 with milestone subtask_ms_1",
                milestones=[subtask_ms_1],
                parent_task=parent_task["_id"],
            )
            created_tasks.append(subtask1)
            subtask1_id = subtask1["_id"]

        with allure.step('Создание второй подзадачи с milestone subtask_ms_2'):
            subtask2 = create_task_in_main(
                "owner_client",
                name="Subtask 2 with milestone subtask_ms_2",
                milestones=[subtask_ms_2],
                parent_task=parent_task["_id"],
            )
            created_tasks.append(subtask2)
            subtask2_id = subtask2["_id"]

        with allure.step('Создание третьей подзадачи без milestone'):
            subtask3 = create_task_in_main(
                "owner_client",
                name="Subtask 3 without milestone",
                milestones=[],
                parent_task=parent_task["_id"],
            )
            created_tasks.append(subtask3)
            subtask3_id = subtask3["_id"]

        # Проверяем задачи в milestone parent_ms_1 (должна быть родительская задача)
        with allure.step('Проверка задач в milestone parent_ms_1(должна быть родительская задача)'):
            tasks_in_parent_ms = get_milestone_tasks(owner_client, main_space, parent_ms_1)
            task_ids = tasks_in_parent_ms["tasks"]
            with allure.step('Проверяем, что родительская задача есть в milestone parent_ms_1'):
                assert parent_task_id in tasks_in_parent_ms["tasks"] # список _id задач
                # Подзадачи с другими milestone быть не должны
            with allure.step('Проверяем, что сабтаски с другими milestone отсутствуют'):
                assert subtask1_id not in task_ids
                assert subtask2_id not in task_ids
                assert subtask3_id not in task_ids

        # Проверяем задачи в milestone subtask_ms_1 (должна быть первая подзадача)
        with allure.step('Проверка задач в milestone subtask_ms_1(должна быть первая сабтаска)'):
            tasks_in_subtask_ms_1 = get_milestone_tasks(owner_client, main_space, subtask_ms_1)
            with allure.step('Проверяем, что subtask1 есть в milestone tasks_in_subtask_ms_1'):
                assert subtask1["_id"] in tasks_in_subtask_ms_1["tasks"]
            # Подзадачи с другими milestone быть не должны
            with allure.step('Проверяем, что parent_task и subtask2, subtask3 отсутствуют в milestone'):
                assert parent_task["_id"] not in tasks_in_subtask_ms_1["tasks"]
                assert subtask2["_id"] not in tasks_in_subtask_ms_1["tasks"]
                assert subtask3["_id"] not in tasks_in_subtask_ms_1["tasks"]

        # Проверяем задачи в milestone subtask_ms_2 (должна быть вторая подзадача)
        with allure.step('Проверка задач в milestone subtask_ms_2(должна быть вторая сабтаска)'):
            tasks_in_subtask_ms_2 = get_milestone_tasks(owner_client, main_space, subtask_ms_2)
            with allure.step('Проверяем, что subtask2 есть в milestone tasks_in_subtask_ms_2'):
                assert subtask2["_id"] in tasks_in_subtask_ms_2["tasks"]
            with allure.step('Проверяем, что parent_task и subtask1, subtask3 отсутствуют в milestone'):
                assert parent_task["_id"] not in tasks_in_subtask_ms_2["tasks"]
                assert subtask1["_id"] not in tasks_in_subtask_ms_2["tasks"]
                assert subtask3["_id"] not in tasks_in_subtask_ms_2["tasks"]

    finally:
        with allure.step('Удаление всех созданных задач'):
            for task in created_tasks:
                delete_task_with_retry(owner_client, task["_id"], main_space)