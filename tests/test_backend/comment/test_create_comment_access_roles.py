import allure
import pytest

from test_backend.data.endpoints.Comment.comment_endpoints import create_comment_endpoint
from test_backend.data.endpoints.Comment.assert_comment_payload import assert_comment_payload
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.task_service.utils import get_random_group_id
from tests.test_backend.task_service.conftest import make_task_in_main

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Comment Service")
@allure.suite("Create Comment")
@allure.sub_suite("Access Check")
@pytest.mark.parametrize(
    "client_fixture_name, expected_status_code",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 200),
        ("guest_client", 403),
    ],
    ids=["owner", "manager", "member", "guest"]
)
def test_create_comment_access_roles(
        request, owner_client, main_space, main_board, make_task_in_main,
        client_fixture_name, expected_status_code
):
    """
    Проверяет права доступа при создании комментария к задаче для разных ролей.
    """
    allure.dynamic.title(f"Создание комментария к задаче от роли: {client_fixture_name}")

    # 1. Получаем клиента, от лица которого будем тестировать
    test_client = request.getfixturevalue(client_fixture_name)
    random_group_id = get_random_group_id(owner_client, main_board, main_space)

    with allure.step("Setup: Создаем базовую задачу от лица владельца (Owner)"):
        task = make_task_in_main({
            "name": f"Task for comment from {client_fixture_name}",
            "group": random_group_id
        })
        task_id = task["_id"]

    with allure.step("Setup: Получаем ID документа, привязанного к задаче"):
        # Информацию о задаче запрашиваем от овнера, нам просто нужен ID её документа
        task_resp = owner_client.post(**get_task_endpoint(slug_id=task_id, space_id=main_space))
        assert task_resp.status_code == 200, f"Ошибка получения задачи: {task_resp.text}"

        target_document_id = task_resp.json()['payload']['task']['document']
        assert target_document_id is not None, "У задачи отсутствует поле 'document'!"

    comment_text = f"Hello! This is a test comment from {client_fixture_name}."

    with allure.step(f"Действие: Отправляем запрос PostComment от роли {client_fixture_name}"):
        resp = test_client.post(
            **create_comment_endpoint(
                space_id=main_space,
                document_id=target_document_id,
                content=comment_text,
                file_ids=[]  # Файлов нет
            )
        )

    with allure.step(f"Проверка: Ожидаемый статус ответа ({expected_status_code})"):
        assert resp.status_code == expected_status_code, \
            f"Ожидался статус {expected_status_code}, но получен {resp.status_code}. Ответ: {resp.text}"

    # Если ожидаем успешное создание, дополнительно проверяем структуру и payload
    if expected_status_code == 200:
        with allure.step("Проверка: Валидируем структуру созданного комментария (IComment)"):
            body = resp.json()
            assert "payload" in body and "comment" in body["payload"], "Отсутствует payload.comment в ответе!"

            created_comment = body["payload"]["comment"]

            assert_comment_payload(
                comment=created_comment,
                expected_document_id=target_document_id,
                expected_content=comment_text
            )
    else:
        with allure.step("Проверка: Бэкенд возвращает корректный формат ошибки (AccessDenied)"):
            error_data = resp.json()
            assert "error" in error_data, "В ответе нет объекта 'error'"
            # Обычно для гостей возвращается ошибка AccessDenied
            assert error_data.get("error", {}).get("code") == "AccessDenied"