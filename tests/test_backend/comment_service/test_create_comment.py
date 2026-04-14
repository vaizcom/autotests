import random
from urllib import request

import allure
import pytest

from test_backend.data.endpoints.Comment.comment_endpoints import create_comment_endpoint
from test_backend.data.endpoints.Comment.assert_comment_payload import assert_comment_payload
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.task_service.conftest import create_task_in_main
from test_backend.task_service.utils import get_client, get_random_group_id

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Comment Service")
@allure.suite("Create Comment")
@allure.title("Smoke Test: Создание комментария к задаче")
def test_create_comment_smoke(owner_client, main_space,  main_board, main_project, create_task_in_main):
    """
    Проверяет успешное создание базового комментария к задаче (documentId) без файлов.
    """
    random_group_id = get_random_group_id(owner_client, main_board, main_space)
    index_task = 0

    with allure.step(f"Создаем задачу от пользователя: {owner_client}"):
        task = create_task_in_main(
            client_fixture=owner_client,
            group=random_group_id,
            index=index_task
        )
        task_id = task["_id"]

    comment_text =  "Hello! This is a smoke test comment."

    with allure.step("Setup: Получаем ID документа, привязанного к задаче"):
        # Запрашиваем информацию о задаче, чтобы вытащить ID её документа
        task_resp = owner_client.post(**get_task_endpoint(slug_id=task_id, space_id=main_space))
        assert task_resp.status_code == 200, f"Ошибка получения задачи: {task_resp.text}"

        target_document_id = task_resp.json()['payload']['task']['document']
        assert target_document_id is not None, "У задачи отсутствует поле 'document'!"

    with allure.step(f"1. Отправляем запрос CreateComment для задачи {target_document_id}"):
        resp = owner_client.post(
            **create_comment_endpoint(
                space_id=main_space,
                document_id=target_document_id,
                content=comment_text,
                file_ids=[]  # Файлов нет
            )
        )

    with allure.step("2. Проверяем статус ответа (200 OK)"):
        assert resp.status_code == 200, f"Ошибка создания комментария: {resp.text}"

    with allure.step("3. Валидируем структуру и данные созданного комментария (IComment)"):
        body = resp.json()
        assert "payload" in body and "comment" in body["payload"], "Отсутствует payload.comment в ответе!"

        created_comment = body["payload"]["comment"]

        assert_comment_payload(
            comment=created_comment,
            expected_document_id=target_document_id,
            expected_content=comment_text
        )