import allure
import pytest

from core.response_utils import short_resp

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Доступ по ролям")
@pytest.mark.parametrize("client_fixture", [
    "owner_client",
    "manager_client",
    "member_client",
    "guest_client",
], ids=["owner", "manager", "member", "guest"])
@pytest.mark.parametrize("kind,kind_id_fixture,entity", [
    ("Space",     "main_space",                  "Space"),
    ("Project",   "main_project",                "Project"),
    ("Task",      "task_id_list",                "Task"),
    ("Milestone", "milestone_id_on_main_board",  "Milestone"),
    ("Document",  "main_space_doc",              "Space document"),
    ("Document",  "main_project_doc",            "Project document"),
], ids=["space", "project", "task", "milestone", "space_doc", "project_doc"])
def test_get_history_roles_with_access(
    request, main_space, client_fixture, kind, kind_id_fixture, entity,
):
    """Все роли (Owner, Manager, Member, Guest) имеют доступ к истории
    сущностей на уровне спейса, проекта и борды."""
    client = request.getfixturevalue(client_fixture)
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(f"{client_fixture}: доступ к {entity} → 200")

    with allure.step(f"Участник: {client_fixture} (полный доступ к спейсу, проекту и борде)"):
        pass

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}' ({entity}) от имени {client_fixture}"):
        resp = client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 200 (OK)"):
        assert resp.status_code == 200, f"Ожидали 200 (OK), получили: {short_resp(resp)}"
