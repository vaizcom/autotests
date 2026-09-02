import allure
import pytest

from test_public_api.data.endpoints.public_history_endpoint import public_history_endpoint

pytestmark = [pytest.mark.public_api]


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("History Kinds")
@pytest.mark.parametrize("kind, kind_id_fixture", [
    ("Space",     "public_space_id"),
    ("Project",   "project_id"),
    ("Task",      "task_id"),
    ("Milestone", "milestone_id"),
    ("Document",  "document_id"),
], ids=["Space", "Project", "Task", "Milestone", "Document"])
def test_public_history_kind_returns_200(request, public_client, public_space_id, kind, kind_id_fixture):
    """
    Проверяем что GetHistory возвращает 200 и непустой items для каждого kind.
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    allure.dynamic.title(f"GetHistory kind='{kind}' возвращает 200 и items ({kind})")

    with allure.step(f"Отправляем GET /public/v1/history с kind='{kind}'"):
        resp = public_client.get(
            **public_history_endpoint(space_id=public_space_id, kind=kind, kind_id=kind_id)
        )

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    body = resp.json()

    with allure.step("Ответ содержит 'items' (список)"):
        assert isinstance(body.get("items"), list), f"'items' должен быть списком: {body}"

    with allure.step("items не пустой — есть хотя бы одно событие"):
        assert len(body["items"]) > 0, f"items пустой для kind='{kind}', kindId='{kind_id}'"

    with allure.step("Каждый item содержит обязательные поля"):
        for item in body["items"][:5]:
            for field in ("_id", "key", "createdAt", "type", "data", "creatorId"):
                assert field in item, f"item без поля '{field}': {item}"
