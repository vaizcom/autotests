import allure
from datetime import datetime
import pytest
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.title("GetTasks dueStart: Проверяет фильтр dueStart")
def test_get_tasks_due_start(main_space, owner_client, board_with_10000_tasks):
    """
    Проверяет, что фильтр `dueStart` корректно включает задачи,
    дата выполнения которых точно совпадает с `dueStart` (или позже),
    и исключает задачи с более ранней датой выполнения.
    В ответе всегда указан интервал дат, т.к. указав только дату (не интервал дат) она интерпритируется как dueEnd
    """
    due_start_str = "2025-12-05T21:00:00.000Z"
    due_start_datetime = datetime.fromisoformat(due_start_str.replace("Z", "+00:00"))

    with allure.step("Запрашиваем задачи с dueStart"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            dueStart=due_start_str,
            sortCriteria="dueStart",
            sortDirection=1))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

        with allure.step("Проверяем, что все задачи имеют due_date >= dueStart"):
            for task in tasks:
                task_due_date_str = task.get("dueStart")
                assert task_due_date_str is not None, f"Задача {task.get('id')} не имеет поля dueStart"

                # Парсим дату задачи из ISO формата
                task_due_date_datetime = datetime.fromisoformat(task_due_date_str.replace("Z", "+00:00"))

                # Проверяем, что дата выполнения задачи не раньше dueStart
                assert task_due_date_datetime >= due_start_datetime, \
                    f"Задача {task.get('id')} имеет dueDate {task_due_date_str}, " \
                    f"которая раньше указанной dueStart {due_start_str}"


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.title("GetTasks dueEnd: Проверяет фильтр dueEnd")
@pytest.mark.skip(reason="Тест skip из-за бага APP-3983")
def test_get_tasks_due_end(main_space, owner_client, board_with_10000_tasks):
    """
    Проверяет, что фильтр `dueEnd` корректно включает задачи,
    дата выполнения которых точно совпадает с `dueEnd` (или раньше),
    и исключает задачи с более поздней датой выполнения.
    """
    due_end_str = "2025-12-05T12:00:00.000Z"
    due_end_datetime = datetime.fromisoformat(due_end_str.replace("Z", "+00:00"))

    with allure.step("Запрашиваем задачи с dueEnd"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            dueEnd=due_end_str,
            sortCriteria="dueEnd",
            sortDirection=1))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

        with allure.step(f"Проверяем, что все задачи имеют due_date <= {due_end_str}"):
            for task in tasks:
                task_due_date_str = task.get("dueEnd")
                assert task_due_date_str is not None, f"Задача {task.get('id')} не имеет поля dueEnd"

                # Парсим дату задачи из ISO формата
                task_due_date_datetime = datetime.fromisoformat(task_due_date_str.replace("Z", "+00:00"))

                # Проверяем, что дата выполнения задачи не позже dueEnd
                assert task_due_date_datetime <= due_end_datetime, \
                    f"Задача {task.get('id')} имеет dueDate {task_due_date_str}, " \
                    f"которая позже указанной dueEnd {due_end_str}"

#   TO DO : после исправления бага APP-3983 добавть тест в котором будет передан интервал дат (dueStart/dueEnd)