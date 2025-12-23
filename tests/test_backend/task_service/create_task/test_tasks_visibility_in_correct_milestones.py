
import allure
import pytest

from test_backend.task_service.utils import delete_task_with_retry, get_milestone_id, create_parent_and_subtasks

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Create Task")
@allure.title('Create Task: Проверка что все задачи корректно видны в соответствующих milestones.')
def test_tasks_visibility_in_correct_milestones(create_task_in_main, owner_client, main_space, main_board):
    """
    Создаём родительскую задачу с milestone parent_ms_1,
    затем три подзадачи:
    - первая с milestone subtask_ms_1
    - вторая с milestone subtask_ms_2
    - третья без milestone
    Проверяем, что все задачи корректно видны в соответствующих milestones.
    """

    created_tasks = []

    try:
        # Используем create_parent_and_subtasks для создания задач
        task_ids, milestones  = create_parent_and_subtasks(
            create_task_in_main=create_task_in_main,
            client_fixture="owner_client",
            owner_client=owner_client,
            main_space=main_space,
            main_board=main_board,
        )
        parent_task_id = task_ids["parent"]
        subtask1_id = task_ids["subtask1"]
        subtask2_id = task_ids["subtask2"]
        subtask3_id = task_ids["subtask3"]

        created_tasks = list(task_ids.values())

        # Получаем milestone'ы для проверки
        parent_ms_1 = milestones["parent_ms_1"]
        subtask_ms_1 = milestones["subtask_ms_1"]
        subtask_ms_2 = milestones["subtask_ms_2"]

        # Проверяем задачи в milestone parent_ms_1 (должна быть родительская задача)
        with allure.step('Проверка задач в milestone parent_ms_1(должна быть родительская задача)'):
            tasks_in_parent_ms = get_milestone_id(owner_client, main_space, parent_ms_1)
            task_ids = tasks_in_parent_ms["tasks"]
            with allure.step('Проверяем, что родительская задача есть в milestone parent_ms_1'):
                assert parent_task_id in task_ids # список _id задач
                # Подзадачи с другими milestone быть не должны
            with allure.step('Проверяем, что сабтаски с другими milestone отсутствуют'):
                assert subtask1_id not in task_ids
                assert subtask2_id not in task_ids
                assert subtask3_id not in task_ids

        # Проверяем задачи в milestone subtask_ms_1 (должна быть первая подзадача)
        with allure.step('Проверка задач в milestone subtask_ms_1(должна быть первая сабтаска)'):
            tasks_in_subtask_ms_1 = get_milestone_id(owner_client, main_space, subtask_ms_1)
            with allure.step('Проверяем, что subtask1 есть в milestone tasks_in_subtask_ms_1'):
                assert subtask1_id in tasks_in_subtask_ms_1["tasks"]
            # Подзадачи с другими milestone быть не должны
            with allure.step('Проверяем, что parent_task и subtask2, subtask3 отсутствуют в milestone'):
                assert parent_task_id not in tasks_in_subtask_ms_1["tasks"]
                assert subtask2_id not in tasks_in_subtask_ms_1["tasks"]
                assert subtask3_id not in tasks_in_subtask_ms_1["tasks"]

        # Проверяем задачи в milestone subtask_ms_2 (должна быть вторая подзадача)
        with allure.step('Проверка задач в milestone subtask_ms_2(должна быть вторая сабтаска)'):
            tasks_in_subtask_ms_2 = get_milestone_id(owner_client, main_space, subtask_ms_2)
            with allure.step('Проверяем, что subtask2 есть в milestone tasks_in_subtask_ms_2'):
                assert subtask2_id in tasks_in_subtask_ms_2["tasks"]
            with allure.step('Проверяем, что parent_task и subtask1, subtask3 отсутствуют в milestone'):
                assert parent_task_id not in tasks_in_subtask_ms_2["tasks"]
                assert subtask1_id not in tasks_in_subtask_ms_2["tasks"]
                assert subtask3_id not in tasks_in_subtask_ms_2["tasks"]

    finally:
        with allure.step('Удаление всех созданных задач'):
            for task in created_tasks:
                delete_task_with_retry(owner_client, task, main_space)