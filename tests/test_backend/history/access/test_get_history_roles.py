import allure
import pytest

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Positive: GetHistory — доступ по ролям")
@pytest.mark.parametrize("client_fixture", [
    "owner_client",
    "manager_client",
    "member_client",
    "guest_client",
], ids=["owner", "manager", "member", "guest"])
@pytest.mark.parametrize("kind,kind_id_fixture,entity", [
    ("Space",    "main_space",       "Space"),
    ("Project",  "main_project",     "Project"),
    ("Document", "main_space_doc",   "Space document"),
    ("Document", "main_project_doc", "Project document"),
], ids=["space", "project", "space_doc", "project_doc"])
def test_get_history_roles_with_access(
    request, main_space, client_fixture, kind, kind_id_fixture, entity,
):
    """Все роли (Owner, Manager, Member, Guest) имеют доступ к истории
    сущностей на уровне спейса и проекта."""
    client = request.getfixturevalue(client_fixture)
    kind_id = request.getfixturevalue(kind_id_fixture)

    allure.dynamic.title(f"GetHistory: {client_fixture} → {entity} → 200")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}' ({entity}) от имени {client_fixture}"):
        resp = client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 200"):
        assert resp.status_code == 200
