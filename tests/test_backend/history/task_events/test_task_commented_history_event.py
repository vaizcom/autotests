import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.data.endpoints.Comment.comment_endpoints import create_comment_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("TASK_COMMENTED event")
def test_task_commented_history_event(main_client, space_for_history, temp_task):
    """
    Проверяем генерацию события TASK_COMMENTED при добавлении комментария к задаче.

    Событие пишется бэкендом с kind=Task и возвращается GetHistory.
    На фронте оно фильтруется из вкладки Activities (DocumentActivity.tsx),
    т.к. комментарии отображаются отдельно на вкладке Comments — это ожидаемое поведение.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task

    with allure.step("1. Получаем document ID задачи"):
        task_resp = main_client.post(**get_task_endpoint(slug_id=task_id, space_id=space_id))
        assert task_resp.status_code == 200, f"Ошибка получения задачи: {task_resp.text}"

        target_document_id = task_resp.json()['payload']['task']['document']
        assert target_document_id, "У задачи отсутствует поле 'document'!"

    with allure.step("2. Создаём комментарий к задаче"):
        comment_text = "Test comment for history event"
        comment_resp = main_client.post(
            **create_comment_endpoint(
                space_id=space_id, document_id=target_document_id,
                content=comment_text, file_ids=[]
            )
        )
        assert comment_resp.status_code == 200, f"Ошибка создания комментария: {comment_resp.text}"

        with allure.step("Проверяем событие TASK_COMMENTED: получено и содержит верные данные (_id, name, text)"):
            assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_COMMENTED",
                expected_data={"_id": task_id, "name": _TASK_NAME, "text": comment_text},
            )
