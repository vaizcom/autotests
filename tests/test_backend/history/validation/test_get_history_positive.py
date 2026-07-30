import allure
import pytest

from test_backend.data.endpoints.History.assert_history_payload import (
    assert_history_schema,
    assert_history_kind_fields,
)

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@pytest.mark.parametrize("kind,kind_id_fixture", [
    ("Space",     "main_space"),
    ("Project",   "main_project"),
    ("Task",      "temp_task_on_temp_board"),
    ("Document",  "main_space_doc"),
    ("Milestone", "temp_milestone_on_temp_board"),
])
def test_get_history_response_structure(request, main_client, main_space, kind, kind_id_fixture):
    """
    Проверяем что каждое событие в ответе содержит:
    - обязательные общие поля: _id, creatorId, createdAt, key, type, data
    - kind-специфичные поля согласно KIND_REQUIRED_FIELDS (APP-5670)
    "Task":      ["taskId", "boardId", "projectId", "spaceId", "creatorId"],
    "Board":     ["boardId", "projectId", "spaceId", "creatorId"],
    "Milestone": ["milestoneId", "boardId", "projectId", "spaceId", "creatorId"],
    "Project":   ["projectId", "spaceId", "creatorId"],
    "Space":     ["spaceId", "creatorId"],
    "Document":  ["documentId", "creatorId"],
    "Member":    ["creatorId"]
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(f"GetHistory: структура событий для kind='{kind}'")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}', kindId='{kind_id}'"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 200, в ответе есть события"):
        assert resp.status_code == 200
        items = resp.json()["payload"]["items"]
        assert len(items) > 0, "Ожидается хотя бы одно событие в истории"

    with allure.step("Проверяем структуру каждого события"):
        for item in items:
            assert_history_schema(item)
            assert_history_kind_fields(item, kind)
