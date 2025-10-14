import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import (
    delete_task_endpoint,
    get_task_endpoint,
)

pytestmark = [pytest.mark.backend]


def test_subtask_parent_child_relationships(
    owner_client, main_space, create_task_in_main
):
    """
    тест проверяет связи родительской задачи и подзадачи через get_task_endpoint,
    а также корректное заполнение полей 'parentTask' и 'subtasks'.
    """
    parent_id = subtask_id = None

    # Создаём родительскую задачу и подзадачу, чтобы проверить связи
    with allure.step("Создание родительской задачи через owner_client"):
        parent_task = create_task_in_main(
            "owner_client",
            name="Parent task for relationship check"
        )
        parent_id = parent_task["_id"]
        parent_slug = parent_task["hrid"]

    try:
        with allure.step("Создание подзадачи через owner_client"):
            subtask = create_task_in_main(
                "owner_client",
                name="Subtask for relationship check",
                parent_task=parent_id
            )
            subtask_id = subtask["_id"]
            subtask_slug = subtask["hrid"]

        with allure.step('Проверяем родительскую задачу через get_task_endpoint'):
            resp_parent = owner_client.post(**get_task_endpoint(slug_id=parent_slug, space_id=main_space))
            assert resp_parent.status_code == 200, f'Не удалось получить родительскую задачу: {resp_parent.status_code}'
            parent = resp_parent.json()["payload"].get("task")
            assert parent is not None, f"Родительская задача (slug={parent_slug}) не найдена"

        with allure.step('Проверяем подзадачу через get_task_endpoint'):
            resp_sub = owner_client.post(**get_task_endpoint(slug_id=subtask_slug, space_id=main_space))
            assert resp_sub.status_code == 200, f'Не удалось получить подзадачу: {resp_sub.status_code}'
            sub = resp_sub.json()["payload"].get("task")
            assert sub is not None, f"Подзадача (slug={subtask_slug}) не найдена"

        with allure.step("Проверяем что у родителя есть подзадача (subtasks), но нет parentTask"):
            assert subtask_id in parent.get("subtasks", []), \
                f"subtask_id {subtask_id} не найден в subtasks родителя: {parent.get('subtasks', [])}"
            assert parent.get("parentTask") is None, \
                f"parentTask у родителя должен быть None, сейчас: {parent.get('parentTask')}"

        with allure.step("Проверяем что у сабтаски есть parentTask и пустой subtasks"):
            assert sub.get("parentTask") == parent_id, \
                f"parentTask у сабтаски должен быть {parent_id}, сейчас: {sub.get('parentTask')}"
            assert sub.get("subtasks", []) == [], \
                f"subtasks у сабтаски должен быть пустым списком, сейчас: {sub.get('subtasks')}"

    finally:
        if subtask_id:
            with allure.step(f"Удаляем сабтаску {subtask_id}"):
                resp = owner_client.post(**delete_task_endpoint(task_id=subtask_id, space_id=main_space))
                assert resp.status_code == 200, f"Не удалось удалить сабтаску {subtask_id}: {resp.text}"
        if parent_id:
            with allure.step(f"Удаляем родительскую задачу {parent_id}"):
                resp = owner_client.post(**delete_task_endpoint(task_id=parent_id, space_id=main_space))
                assert resp.status_code == 200, f"Не удалось удалить родителя {parent_id}: {resp.text}"