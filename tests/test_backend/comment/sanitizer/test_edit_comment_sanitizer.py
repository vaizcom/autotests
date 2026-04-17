import allure
import pytest

from test_backend.data.endpoints.Comment.comment_endpoints import (
    create_comment_endpoint,
    edit_comment_endpoint,
    get_comments_endpoint,
)

pytestmark = [pytest.mark.backend]

EDIT_SANITIZED_CASES = [
    pytest.param(
        "<p><b>formatted</b></p>",
        "<p>1</p><p>2</p><p>3</p>",
        "<p>1</p><p>2</p><p>3</p>",
        200,
        "Сброс форматирования — plain текст сохраняется",
        id="reset_style_plain_paragraphs"
    ),
    pytest.param(
        "<p>original</p>",
        "<script>alert('xss')</script>",
        None,
        400,
        "Тег script при редактировании → 400, пустой контент отклоняется",
        id="edit_script_tag_stripped_returns_400"
    ),
    pytest.param(
        "<p>original</p>",
        "<p onclick=\"evil()\">edited</p>",
        "<p>edited</p>",
        200,
        "Атрибут onclick при редактировании удаляется",
        id="edit_onclick_removed"
    ),
]


@allure.parent_suite("Comment Service")
@allure.suite("Sanitizer")
@allure.sub_suite("Edit comment")
@pytest.mark.parametrize("initial_content,edit_content,expected_content,expected_status,title", EDIT_SANITIZED_CASES)
def test_edit_comment_content_sanitized(
        owner_client, main_space, document_id,
        initial_content, edit_content, expected_content, expected_status, title
):
    """
    Санитайзер применяется и при редактировании комментария через EditComment.
    """
    allure.dynamic.title(title)

    with allure.step("Создаём исходный комментарий"):
        create_resp = owner_client.post(
            **create_comment_endpoint(
                space_id=main_space,
                document_id=document_id,
                content=initial_content,
            )
        )
        assert create_resp.status_code == 200, f"Ошибка создания комментария: {create_resp.text}"
        comment_id = create_resp.json()["payload"]["comment"]["_id"]

    with allure.step(f"Редактируем комментарий через EditComment (ожидаем {expected_status})"):
        edit_resp = owner_client.post(
            **edit_comment_endpoint(
                space_id=main_space,
                comment_id=comment_id,
                content=edit_content,
            )
        )
        assert edit_resp.status_code == expected_status, (
            f"Ожидался статус {expected_status}, получен {edit_resp.status_code}. Ответ: {edit_resp.text}"
        )

    if expected_status == 200:
        with allure.step("Получаем комментарий через GetComments"):
            comments_resp = owner_client.post(
                **get_comments_endpoint(space_id=main_space, document_id=document_id)
            )
            assert comments_resp.status_code == 200, f"Ошибка GetComments: {comments_resp.text}"
            comments = comments_resp.json()["payload"]["comments"]
            comment = next((c for c in comments if c["_id"] == comment_id), None)
            assert comment is not None, f"Комментарий {comment_id} не найден в GetComments"

        with allure.step("Проверяем content после редактирования"):
            actual_content = comment["content"]
            assert actual_content == expected_content, (
                f"Санитайзер при EditComment отработал иначе, чем ожидалось!\n"
                f"Отправлено:  {edit_content!r}\n"
                f"Ожидалось:   {expected_content!r}\n"
                f"Получено:    {actual_content!r}"
            )