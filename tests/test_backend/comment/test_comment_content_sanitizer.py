import allure
import pytest

from test_backend.data.endpoints.Comment.comment_endpoints import create_comment_endpoint, get_comments_endpoint, edit_comment_endpoint
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from tests.test_backend.task_service.conftest import make_task_in_main

pytestmark = [pytest.mark.backend]

# ---------------------------------------------------------------------------
# Позитивные сценарии: разрешённый контент должен сохраняться без изменений
# ---------------------------------------------------------------------------
ALLOWED_CONTENT_CASES = [
    pytest.param(
        "<p>Hello world</p>",
        id="p_tag"
    ),
    pytest.param(
        "<b>bold</b> and <i>italic</i> and <u>underline</u> and <s>strike</s>",
        id="inline_formatting"
    ),
    pytest.param(
        '<a href="https://example.com" target="_blank">link</a>',
        id="anchor_with_href_target"
    ),
    pytest.param(
        '<img src="https://example.com/img.png" alt="image" />',
        id="img_with_src_alt"
    ),
    pytest.param(
        '<p class="my-class" id="p1">styled paragraph</p>',
        id="global_attrs_class_id"
    ),
    pytest.param(
        '<ul data-type="taskList"><li data-checked="true">done</li></ul>',
        id="task_list_with_data_checked"
    ),
    pytest.param(
        '<ol start="5"><li>item 5</li></ol>',
        id="ordered_list_with_start"
    ),
    pytest.param(
        "<code>const x = 1;</code>",
        id="code_tag"
    ),
    pytest.param(
        "<pre><code>multiline\ncode</code></pre>",
        id="pre_code"
    ),
    pytest.param(
        "<mark>highlighted text</mark>",
        id="mark_tag"
    ),
    pytest.param(
        "<blockquote><p>quoted text</p></blockquote>",
        id="blockquote"
    ),
    pytest.param(
        '<block-custom-mention data="123" inline="true">@user</block-custom-mention>',
        id="block_custom_mention"
    ),
    pytest.param(
        '<block-custom-mention-v2 data="456" inline="false">@team</block-custom-mention-v2>',
        id="block_custom_mention_v2"
    ),
    pytest.param(
        '<em-emoji shortcodes=":smile:" class="emoji"></em-emoji>',
        id="em_emoji"
    ),
    pytest.param(
        "<table><thead><tr><th>Col</th></tr></thead><tbody><tr><td>Val</td></tr></tbody></table>",
        id="table_structure"
    ),
    pytest.param(
        "<ul><li>item one</li><li>item two</li></ul>",
        id="bullet_list"
    ),
    pytest.param(
        "<p>1<br />2<br />3</p><p></p>",
        id="merge_paragraph_with_br"
    ),
]

# ---------------------------------------------------------------------------
# Негативные сценарии: запрещённый контент должен быть удалён/обрезан
# ---------------------------------------------------------------------------
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
@allure.sub_suite("Allowed content")
@pytest.mark.parametrize("content", ALLOWED_CONTENT_CASES)
def test_comment_allowed_content_preserved(
        owner_client, main_space, main_board, make_task_in_main, content
):
    """
    Разрешённые теги и атрибуты должны сохраняться в content комментария без изменений.
    """
    allure.dynamic.title(f"Allowed: {content[:60]}")

    task = make_task_in_main({"name": "Task for sanitizer test (allowed)"})
    task_id = task["_id"]

    task_resp = owner_client.post(**get_task_endpoint(slug_id=task_id, space_id=main_space))
    assert task_resp.status_code == 200
    document_id = task_resp.json()["payload"]["task"]["document"]

    with allure.step("Отправляем комментарий с разрешённым HTML"):
        resp = owner_client.post(
            **create_comment_endpoint(
                space_id=main_space,
                document_id=document_id,
                content=content,
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

    with allure.step("Проверяем, что content сохранился без изменений"):
        actual_content = comment["content"]
        assert actual_content == content, (
            f"Контент изменился после санитизации!\n"
            f"Отправлено:  {content!r}\n"
            f"Получено:    {actual_content!r}"
        )


@allure.parent_suite("Comment Service")
@allure.suite("Sanitizer")
@allure.sub_suite("Blocked content")
@pytest.mark.parametrize("input_content,expected_content", SANITIZED_CONTENT_CASES)
def test_comment_blocked_content_sanitized(
        owner_client, main_space, main_board, make_task_in_main, input_content, expected_content
):
    """
    Запрещённые теги и атрибуты должны быть удалены из content комментария.
    """
    allure.dynamic.title(f"Blocked: {input_content[:60]}")

    task = make_task_in_main({"name": "Task for sanitizer test (blocked)"})
    task_id = task["_id"]

    task_resp = owner_client.post(**get_task_endpoint(slug_id=task_id, space_id=main_space))
    assert task_resp.status_code == 200
    document_id = task_resp.json()["payload"]["task"]["document"]

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


# ---------------------------------------------------------------------------
# EditComment: санитайзер работает и при редактировании
# ---------------------------------------------------------------------------

EDIT_SANITIZED_CASES = [
    pytest.param(
        "<p><b>formatted</b></p>",
        "<p>1</p><p>2</p><p>3</p>",
        "<p>1</p><p>2</p><p>3</p>",
        200,
        id="reset_style_plain_paragraphs"
    ),
    pytest.param(
        "<p>original</p>",
        "<script>alert('xss')</script>",
        None,
        400,
        id="edit_script_tag_stripped_returns_400"
    ),
    pytest.param(
        "<p>original</p>",
        "<p onclick=\"evil()\">edited</p>",
        "<p>edited</p>",
        200,
        id="edit_onclick_removed"
    ),
]


@allure.parent_suite("Comment Service")
@allure.suite("Sanitizer")
@allure.sub_suite("Edit comment")
@pytest.mark.parametrize("initial_content,edit_content,expected_content,expected_status", EDIT_SANITIZED_CASES)
def test_edit_comment_content_sanitized(
        owner_client, main_space, main_board, make_task_in_main,
        initial_content, edit_content, expected_content, expected_status
):
    """
    Санитайзер применяется и при редактировании комментария через EditComment.
    """
    allure.dynamic.title(f"Edit: {edit_content[:60]}")

    task = make_task_in_main({"name": "Task for edit comment sanitizer test"})
    task_id = task["_id"]

    task_resp = owner_client.post(**get_task_endpoint(slug_id=task_id, space_id=main_space))
    assert task_resp.status_code == 200
    document_id = task_resp.json()["payload"]["task"]["document"]

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
