import allure
import pytest

from test_backend.data.endpoints.Comment.comment_endpoints import create_comment_endpoint, get_comments_endpoint

pytestmark = [pytest.mark.backend]

SANITIZED_CONTENT_CASES = [
    pytest.param(
        "<script>alert('xss')</script>",
        "<p></p>",
        id="script_tag_stripped"
    ),
    pytest.param(
        "<iframe src='https://evil.com'></iframe>",
        "<p></p>",
        id="iframe_tag_stripped"
    ),
    pytest.param(
        "<form action='https://evil.com'><input type='submit'></form>",
        '<input type="submit" />',
        id="form_tag_stripped_input_preserved"
    ),
    pytest.param(
        "<p onclick=\"alert('xss')\">click me</p>",
        "<p>click me</p>",
        id="onclick_attr_removed"
    ),
    pytest.param(
        "<img src='x' onerror=\"alert('xss')\">",
        '<img src="x" />',
        id="onerror_attr_removed"
    ),
    pytest.param(
        "<a href=\"javascript:alert('xss')\">click</a>",
        '<a target="_blank">click</a>',
        id="javascript_href_removed"
    ),
    pytest.param(
        "<div><script>evil()</script>safe content</div>",
        "<div>safe content</div>",
        id="script_inside_div_stripped"
    ),
    pytest.param(
        "<p data-custom=\"evil\" data-inject=\"payload\">text</p>",
        "<p>text</p>",
        id="unknown_data_attrs_removed"
    ),
    pytest.param(
        "<svg><use xlink:href=\"#evil\"/></svg>",
        "<p></p>",
        id="svg_tag_stripped"
    ),
    pytest.param(
        "<object data=\"evil.swf\"></object>",
        "<p></p>",
        id="object_tag_stripped"
    ),
    pytest.param(
        '<p class="my-class" style="color:red">styled</p>',
        '<p class="my-class">styled</p>',
        id="style_attr_removed"
    ),
]


@allure.parent_suite("Comment Service")
@allure.suite("Sanitizer")
@allure.sub_suite("Blocked content")
@pytest.mark.parametrize("input_content,expected_content", SANITIZED_CONTENT_CASES)
def test_post_comment_blocked_content_sanitized(
        owner_client, main_space, document_id, input_content, expected_content
):
    """
    Запрещённые теги и атрибуты должны быть удалены из content комментария.
    """
    allure.dynamic.title(f"Blocked: {input_content[:60]}")

    with allure.step("Отправляем комментарий с запрещённым HTML"):
        resp = owner_client.post(
            **create_comment_endpoint(
                space_id=main_space,
                document_id=document_id,
                content=input_content,
            )
        )
        assert resp.status_code == 200, f"Ошибка создания комментария: {resp.text}"
        comment_id = resp.json()["payload"]["comment"]["_id"]

    with allure.step("Получаем комментарий через GetComments"):
        comments_resp = owner_client.post(
            **get_comments_endpoint(space_id=main_space, document_id=document_id)
        )
        assert comments_resp.status_code == 200, f"Ошибка GetComments: {comments_resp.text}"
        comments = comments_resp.json()["payload"]["comments"]
        comment = next((c for c in comments if c["_id"] == comment_id), None)
        assert comment is not None, f"Комментарий {comment_id} не найден в GetComments"

    with allure.step("Проверяем, что запрещённый контент был удалён"):
        actual_content = comment["content"]
        assert actual_content == expected_content, (
            f"Санитайзер отработал иначе, чем ожидалось!\n"
            f"Отправлено:  {input_content!r}\n"
            f"Ожидалось:   {expected_content!r}\n"
            f"Получено:    {actual_content!r}"
        )
