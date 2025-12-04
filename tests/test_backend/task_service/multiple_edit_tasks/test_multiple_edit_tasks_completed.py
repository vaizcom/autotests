import pytest
import allure

from tests.test_backend.data.endpoints.Task.task_endpoints import multiple_edit_tasks_endpoint, get_task_endpoint, create_task_endpoint, delete_task_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("multiple_edit_tasks")
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


@allure.parent_suite("multiple_edit_tasks")
def test_multiple_edit_tasks_sets_completed_only_uncompleted(owner_client, main_space, main_board):
    allure.dynamic.title("Multiple edit Tasks: completed=True меняет только незавершённую таску, завершённая остаётся без изменений")

    """
    Создаём 2 задачи:
    - task_done: заранее ставим completed=True
    - task_todo: оставляем completed=False
    Применяем MultipleEditTasks с completed=True к обеим таскам.
    Проверяем:
    - в payload.success присутствуют task_todo и task_done
    - состояния по get_task: task_done остался True, task_todo стал True
    Удаляем созданные задачи.
    """

    t_true = None
    t_false = None
    try:
        with allure.step("предусловие: Создаём 2 задачи  task_completed_true, task_completed_false"):
            _true = owner_client.post(
                **create_task_endpoint(main_space, board=main_board, completed=True, name="task_completed_true"))
            _false = owner_client.post(
                **create_task_endpoint(main_space, board=main_board, completed=False, name="task_completed_false"))
            t_true = (((_true.json().get("payload") or {}).get("task")) or {}).get("_id")
            t_false = (((_false.json().get("payload") or {}).get("task")) or {}).get("_id")

        with allure.step("Проверяем предусловие корректно выставленных completed: используем для проверки get_task"):
            r_true = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=t_true))
            r_true.raise_for_status()
            t_true_body = ((r_true.json().get("payload") or {}).get("task")) or {}
            assert t_true_body.get(
                "completed") is True, f"task_done должен быть completed=True, получено {t_true_body.get('completed')!r}"

            r_false = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=t_false))
            r_false.raise_for_status()
            r_false_body = ((r_false.json().get("payload") or {}).get("task")) or {}
            assert r_false_body.get(
                "completed") is False, f"task_todo должен быть не завершён, получено {r_false_body.get('completed')!r}"

        with allure.step("Применяем completed=True к обеим задачам через MultipleEditTasks"):
            payload = [
                {"taskId": t_true, "completed": True},
                {"taskId": t_false, "completed": True},
            ]
            resp = owner_client.post(**multiple_edit_tasks_endpoint(space_id=main_space, tasks=payload))
            assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
            body = resp.json() or {}
            payload_body = body.get("payload") or {}
            success = payload_body.get("success") or []
            failed = payload_body.get("failed") or []

        with allure.step("Проверяем, что в success обе задачи, а в failed список пуст"):
            assert (t_true in success) and (t_false in success), f"Обе задачи должны быть в success, success={success}"
            assert (t_true not in failed) and (
                        t_false not in failed), f"Список failed должен быть пуст, failed={failed}"

        with allure.step("Проверяем состояния по get_task после операции"):
            r_done_after = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=t_true))
            r_done_after.raise_for_status()
            t_done_after = ((r_done_after.json().get("payload") or {}).get("task")) or {}
            assert t_done_after.get(
                "completed") is True, f"task_done должен остаться completed=True, получено {t_done_after.get('completed')!r}"

            r_todo_after = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=t_false))
            r_todo_after.raise_for_status()
            t_todo_after = ((r_todo_after.json().get("payload") or {}).get("task")) or {}
            assert t_todo_after.get(
                "completed") is True, f"task_todo должен стать completed=True, получено {t_todo_after.get('completed')!r}"
    finally:
        # Удаляем созданные задачи даже при падении теста
        try:
            if t_true:
                owner_client.post(**delete_task_endpoint(space_id=main_space, task_id=t_true))
        except Exception:
            pass
        try:
            if t_false:
                owner_client.delete(**delete_task_endpoint(space_id=main_space, task_id=t_false))
        except Exception:
            pass