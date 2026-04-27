import json
import allure
import pytest

from test_backend.data.endpoints.Comment.comment_endpoints import create_comment_endpoint, get_comments_endpoint

pytestmark = [pytest.mark.backend]

ALLOWED_CONTENT_CASES = [
    pytest.param(
        "<p>Hello world</p>",
        "Параграф с текстом сохраняется",
        id="p_tag"
    ),
    pytest.param(
        "<b>bold</b> and <i>italic</i> and <u>underline</u> and <s>strike</s>",
        "Жирный, курсив, подчёркнутый, зачёркнутый текст сохраняются",
        id="inline_formatting"
    ),
    pytest.param(
        '<a href="https://example.com" target="_blank" rel="noopener noreferrer">link</a>',
        "Ссылка с href и target=_blank сохраняется (бэкенд добавляет rel=noopener noreferrer)",
        id="anchor_with_href_target"
    ),
    pytest.param(
        '<img src="https://example.com/img.png" alt="image" />',
        "Изображение с src и alt сохраняется",
        id="img_with_src_alt"
    ),
    pytest.param(
        '<p class="my-class" id="p1">styled paragraph</p>',
        "Атрибуты class и id сохраняются",
        id="global_attrs_class_id"
    ),
    pytest.param(
        '<ul data-type="taskList">'
        '<li data-checked="false" data-type="taskItem"><label><input type="checkbox" /><span></span></label><div><p>item 1</p></div></li>'
        '<li data-checked="true" data-type="taskItem"><label><input type="checkbox" checked /><span></span></label><div><p>item 2</p></div></li>'
        '</ul>',
        "Таск-лист с чекбоксами сохраняется",
        id="task_list_with_data_checked"
    ),
    pytest.param(
        '<ol start="5"><li>item 5</li></ol>',
        "Нумерованный список с заданным начальным номером сохраняется",
        id="ordered_list_with_start"
    ),
    pytest.param(
        "<code>const x = 1;</code>",
        "Инлайн-код сохраняется",
        id="code_tag"
    ),
    pytest.param(
        "<pre><code>multiline\ncode</code></pre>",
        "Блок кода сохраняется",
        id="pre_code"
    ),
    pytest.param(
        "<mark>highlighted text</mark>",
        "Выделение текста цветом сохраняется",
        id="mark_tag"
    ),
    pytest.param(
        "<blockquote><p>quoted text</p></blockquote>",
        "Цитата сохраняется",
        id="blockquote"
    ),
    pytest.param(
        '<em-emoji shortcodes=":smile:" class="emoji"></em-emoji>',
        "Эмодзи сохраняется",
        id="em_emoji"
    ),
    pytest.param(
        "<ul><li>item one</li><li>item two</li></ul>",
        "Маркированный список сохраняется",
        id="bullet_list"
    ),
    pytest.param(
        "<p>1<br />2<br />3</p><p></p>",
        "Перенос строки внутри параграфа (Shift+Enter) сохраняется",
        id="soft_line_breaks_with_br"
    ),
    pytest.param(
        "<p>1</p><p></p><p>2</p><p></p><p>3</p>",
        "Несколько параграфов сохраняются",
        id="multiple_paragraphs"
    ),
]


@allure.parent_suite("Comment Service")
@allure.suite("Sanitizer")
@allure.sub_suite("Allowed content")
@pytest.mark.parametrize("content,title", ALLOWED_CONTENT_CASES)
def test_post_comment_allowed_content_preserved(
        owner_client, main_space, document_id, content, title
):
    """
    Разрешённые теги и атрибуты должны сохраняться в content комментария без изменений.
    """
    allure.dynamic.title(title)

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
@allure.sub_suite("Allowed content")
@allure.title("Упоминания пользователей сохраняются")
def test_post_comment_mentions_preserved(owner_client, main_space, document_id, main_personal):
    """
    Упоминания реальных пользователей через block-custom-mention-v2 сохраняются без изменений.
    """
    member_id = main_personal["member"][0]
    manager_id = main_personal["manager"][0]

    def make_mention(user_id: str) -> str:
        data = json.dumps({"item": {"id": user_id, "kind": "User"}}).replace('"', "&quot;")
        return f'<block-custom-mention-v2 custom="1" inline="true" data="{data}"></block-custom-mention-v2>'

    content = f"<p>{make_mention(member_id)} {make_mention(manager_id)}</p>"

    with allure.step("Отправляем комментарий с упоминаниями"):
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

    with allure.step("Проверяем, что упоминания сохранились без изменений"):
        actual_content = comment["content"]
        assert actual_content == content, (
            f"Упоминания изменились после санитизации!\n"
            f"Отправлено:  {content!r}\n"
            f"Получено:    {actual_content!r}"
        )