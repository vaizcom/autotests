import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import (
    delete_task_endpoint,
    get_task_endpoint,
)

pytestmark = [pytest.mark.backend]

@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_create_subtask_per_role(
    owner_client, main_space, main_board, create_task_in_main, client_fixture, expected_status
):
    """
    Тестирование создания подзадачи разными пользовательскими ролями и проверка
    ожидаемого поведения на основе прав доступа роли.

    Этот тест оценивает может ли клиент с разными уровнями доступа создавать
    подзадачу для родительской задачи. Также проверяются корректные связи между
    родительской задачей и подзадачей, включая поля `parentTask` и `subtasks`.

    """
    parent_id = subtask_id = None

    try:
        with allure.step("Создание родительской задачи через owner_client"):
            parent_task = create_task_in_main(
                "owner_client",
                name="Main task for subtask access test"
            )
            parent_id = parent_task["_id"]
            parent_slug = parent_task["hrid"]

        with allure.step(f"Создание сабтаски в роли {client_fixture}"):
            try:
                subtask = create_task_in_main(
                    client_fixture,
                    name=f"Subtask by {client_fixture}",
                    parent_task=parent_id
                )
                subtask_id = subtask["_id"]
                subtask_slug = subtask["hrid"]
                creation_exception = None
            except Exception as exc:
                subtask_id = None
                subtask_slug = None
                creation_exception = exc

        if expected_status == 200:
            assert subtask_id, f"{client_fixture} должен иметь возможность создать сабтаску, но упали с {creation_exception}"

            with allure.step("Проверяем, что в ответе у сабтаски присутствует parentTask с корректным ID."):
                assert subtask.get("parentTask") == parent_id, (
                    f"У созданной сабтаски (ID={subtask_id}) поле parentTask должно быть {parent_id}, "
                    f"но сейчас: {subtask.get('parentTask')}"
                )
            with allure.step("Проверяем что у сабтаски отсутствуют дочерние subtasks"):
                assert subtask.get("subtasks", []) == [], (
                    f"Поле subtasks у сабтаски (ID={subtask_id}) должно быть пустым списком, "
                    f"но сейчас: {subtask.get('subtasks')}"
                )


        else:  # expected_status == 403
            with allure.step(f"Проверяем, что {client_fixture} не может создать сабтаску (expected_status == 403)"):
                assert subtask_id is None, f"{client_fixture} НЕ должен иметь права создавать сабтаску, но задача появилась: {subtask_id}"
                assert creation_exception is not None, "Ожидалось исключение (ошибка запроса), но его не было"

        # Проверка связей: теперь через get_task_endpoint (используя slug)
        with allure.step('Проверяем родительскую задачу через get_task_endpoint'):
            resp_parent = owner_client.post(**get_task_endpoint(slug_id=parent_slug, space_id=main_space))
            assert resp_parent.status_code == 200, f'Не удалось получить родительскую задачу: {resp_parent.status_code}'
            parent = resp_parent.json()["payload"].get("task")
            assert parent is not None, f"Родительская задача (slug={parent_slug}) не найдена"

        if subtask_id:
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
        else:
            with allure.step("Проверяем что у родителя нет сабтасок если их не создалось"):
                assert parent.get("subtasks", []) == [] or parent.get("subtasks", []) is None, \
                    "У родителя не должно быть сабтасок, если их не удалось создать"
    finally:
        if subtask_id:
            with allure.step(f"Удаляем сабтаску {subtask_id}"):
                resp = owner_client.post(**delete_task_endpoint(task_id=subtask_id, space_id=main_space))
                assert resp.status_code == 200, f"Не удалось удалить сабтаску {subtask_id}: {resp.text}"
        if parent_id:
            with allure.step(f"Удаляем родительскую задачу {parent_id}"):
                resp = owner_client.post(**delete_task_endpoint(task_id=parent_id, space_id=main_space))
                assert resp.status_code == 200, f"Не удалось удалить родителя {parent_id}: {resp.text}"