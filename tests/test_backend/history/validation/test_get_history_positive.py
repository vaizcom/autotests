import allure
import pytest

from test_backend.data.endpoints.History.assert_history_payload import (
    assert_history_schema,
    assert_history_kind_fields,
)

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.sub_suite("Positive")
@pytest.mark.parametrize("kind,kind_id_fixture", [
    ("Space",     "main_space"),
    ("Project",   "main_project"),
    ("Task",      "temp_task_on_temp_board"),
    ("Document",  "main_space_doc"),
    ("Milestone", "temp_milestone_on_temp_board"),
], ids=["space", "project", "task", "document", "milestone"])
def test_get_history_response_structure(request, main_client, main_space, kind, kind_id_fixture):
    """
    Smoke: проверяем структуру первых 5 событий в ответе.
    Каждое событие должно содержать:
    - обязательные общие поля: _id, creatorId, createdAt, key, type, data
    - kind-специфичные поля согласно KIND_REQUIRED_FIELDS (APP-5670)
    "Space":     ["spaceId", "creatorId"],
    "Project":   ["projectId", "spaceId", "creatorId"],
    "Task":      ["taskId", "boardId", "projectId", "spaceId", "creatorId"],
    "Document":  ["documentId", "creatorId"],
    "Milestone": ["milestoneId", "boardId", "projectId", "spaceId", "creatorId"]
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(f"GetHistory: структура событий для kind='{kind}'")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}', kindId='{kind_id}', limit=5"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id, "limit": 5},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 200, в ответе есть события"):
        assert resp.status_code == 200
        items = resp.json()["payload"]["items"]
        assert len(items) > 0, "Ожидается хотя бы одно событие в истории"

    with allure.step(f"Smoke: проверяем структуру первых {len(items)} событий"):
        for item in items:
            assert_history_schema(item)
            assert_history_kind_fields(item, kind)
