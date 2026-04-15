import allure
import pytest

from test_backend.data.endpoints.Comment.comment_endpoints import create_comment_endpoint, get_comments_endpoint

pytestmark = [pytest.mark.backend]

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


@allure.parent_suite("Comment Service")
@allure.suite("Sanitizer")
@allure.sub_suite("Allowed content")
@pytest.mark.parametrize("content", ALLOWED_CONTENT_CASES)
def test_post_comment_allowed_content_preserved(
        owner_client, main_space, document_id, content
):
    """
    Разрешённые теги и атрибуты должны сохраняться в content комментария без изменений.
    """
    allure.dynamic.title(f"Allowed: {content[:60]}")

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
