import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.data.endpoints.Comment.comment_endpoints import create_comment_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task Commented event")
def test_task_commented_history_event(main_client, main_space, temp_task_on_board_with_tasks):
    """
    Проверяем генерацию события TASK_COMMENTED при добавлении комментария к задаче.
    """
    task_id = temp_task_on_board_with_tasks

    with allure.step("1. Получаем document ID задачи"):
        task_resp = main_client.post(**get_task_endpoint(slug_id=task_id, space_id=main_space))
        assert task_resp.status_code == 200, f"Ошибка получения задачи: {task_resp.text}"

        target_document_id = task_resp.json()['payload']['task']['document']
        assert target_document_id, "У задачи отсутствует поле 'document'!"

    with allure.step("2. Создаём комментарий к задаче -> ожидаем TASK_COMMENTED"):
        comment_text = "Test comment for history event"
        comment_resp = main_client.post(
            **create_comment_endpoint(
                space_id=main_space,
                document_id=target_document_id,
                content=comment_text,
                file_ids=[]
            )
        )
        assert comment_resp.status_code == 200, f"Ошибка создания комментария: {comment_resp.text}"

        assert_history_event_exists(
            client=main_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_COMMENTED",
            expected_data={"_id": task_id, "text": comment_text}
        )