import pytest
import allure
from tests.test_backend.data.endpoints.Task.task_endpoints import multiple_edit_tasks_endpoint, get_task_endpoint

pytestmark = [pytest.mark.backend]

@pytest.mark.parametrize(
    "count, expect_status",
    [
        (1, 200),
        (20, 200),
    ],
    ids=["1-task", "20-tasks"],
)
def test_multiple_edit_tasks_completed(owner_client, main_space, create_30_tasks, count, expect_status):
    allure.dynamic.title(f"Multiple Edit Tasks: completed = True/False для {count} задач (ожидаемый статус {expect_status})")
    """
        Флоу:
        1) Создать N задач (1, 20).
        2) Проставить completed=True через MultipleEditTasks (ожидаем 200).
        3) Проверить через get_task, что completed=True.
        4) Снять completed=False и проверить через get_task.
    """

    with allure.step(f"Создаём {count} задач"):
        task_ids = create_30_tasks(count=count)
        assert len(task_ids) == count, f"Ожидали создать {count} задач, создано: {len(task_ids)}"

    with allure.step(f"Устанавливаем completed=True для {count} задач"):
        payload_true = [{"taskId": tid, "completed": True} for tid in task_ids]
        resp_true = owner_client.post(**multiple_edit_tasks_endpoint(space_id=main_space, tasks=payload_true))
        body_true = resp_true.json()

    with allure.step("Проверяем, что ответ корректен и задачи отражены в success"):
        assert resp_true.status_code == 200, f"Ожидали 200 при {count} задачах, получено: {resp_true.status_code}"
        payload = body_true.get("payload") or {}
        success = payload.get("success") or []
        failed = payload.get("failed") or []
        if isinstance(success, list) and isinstance(failed, list):
            missing = [tid for tid in task_ids if tid not in success]
            assert not missing, f"Не все задачи отражены в ответе: {missing}"

    with allure.step("Проверяем через get_task, что completed=True применился"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            r.raise_for_status()
            tb = r.json()
            t = (tb.get("payload") or {}).get("task") or {}
            assert t.get("completed") is True, f"После completed=True задача {tid} имеет completed={t.get('completed')!r}"

    with allure.step("Устанавливаем completed=False для всех задач и проверяем через get_task"):
        payload_false = [{"taskId": tid, "completed": False} for tid in task_ids]
        resp_false = owner_client.post(**multiple_edit_tasks_endpoint(space_id=main_space, tasks=payload_false))
        assert resp_false.status_code == 200, f"Ожидали 200 при снятии completed для {count} задач, получено: {resp_false.status_code}"
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            r.raise_for_status()
            tb = r.json()
            t = (tb.get("payload") or {}).get("task") or tb.get("task") or {}
            assert t.get("completed") is False, f"После completed=False задача {tid} имеет completed={t.get('completed')!r}"


def test_multiple_edit_tasks_completed_limit(owner_client, main_space, create_30_tasks):
    allure.dynamic.title("Multiple Edit Tasks: completed=True для 21 задачи — ожидаем 400 или TooManyTasksSelected")
    with allure.step("Создаём 21 задачу"):
        task_ids = create_30_tasks(count=21)
        assert len(task_ids) == 21, f"Ожидали создать 21 задачу, создано: {len(task_ids)}"

    with allure.step("Пытаемся установить completed=True для 21 задачи"):
        payload_true = [{"taskId": tid, "completed": True} for tid in task_ids]
        resp_true = owner_client.post(**multiple_edit_tasks_endpoint(space_id=main_space, tasks=payload_true))
        body_true = resp_true.json() if resp_true.content else {}

    with allure.step("Проверяем, что пришёл 400 или error.code=TooManyTasksSelected"):
        err = (body_true.get("error") or {}) if body_true else {}
        assert (resp_true.status_code == 400) or (err.get("code") == "TooManyTasksSelected"), (
            f"Ожидали 400 или error.code=TooManyTasksSelected при 21 задаче. "
            f"status={resp_true.status_code}, error={err!r}"
        )