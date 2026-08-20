import allure
import pytest

from core.response_utils import short_resp

pytestmark = [pytest.mark.backend]


# ──────────────────────────────────────────────────────────────────────────────
# 1. Space-only: в спейсе, но без доступа к проекту и борду
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Access matrix")
@pytest.mark.parametrize("kind,kind_id_fixture,entity,expected_status", [
    ("Space",     "main_space",                   "Space",             200),
    ("Document",  "main_space_doc",               "Space document",    200),
    ("Project",   "main_project",                 "Project",           403),
    ("Document",  "main_project_doc",             "Project document",  403),
    ("Document",  "main_personal_doc",            "Member document",   403),
    ("Task",      "task_id_list",                 "Task",              403),
    ("Milestone", "temp_milestone_on_temp_board", "Milestone",         403),
], ids=[
    "space-200",
    "space_doc-200",
    "project-403",
    "project_doc-403",
    "member_doc-403",
    "task-403",
    "milestone-403",
])
def test_get_history_space_only_access(
    request, main_space, kind, kind_id_fixture, entity, expected_status,
):
    """Space-only клиент: видит Space и спейс-документы, не видит Project и ниже."""
    client = request.getfixturevalue("client_with_access_only_in_space")
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    sees = "видит" if expected_status == 200 else "не видит"
    allure.dynamic.title(f"Клиент с доступом к Space: {sees} {entity} → {expected_status}")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}' ({entity}) от имени space_only client"):
        resp = client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step(f"Получаем {expected_status} ({'OK' if expected_status == 200 else 'Forbidden'})"):
        assert resp.status_code == expected_status, f"Ожидали {expected_status} ({'OK' if expected_status == 200 else 'Forbidden'}), получили: {short_resp(resp)}"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Project-only: в спейсе и проекте, но без доступа к борду
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Access matrix")
@pytest.mark.parametrize("kind,kind_id_fixture,entity,expected_status", [
    ("Space",     "main_space",                   "Space",             200),
    ("Document",  "main_space_doc",               "Space document",    200),
    ("Project",   "main_project",                 "Project",           200),
    ("Document",  "main_project_doc",             "Project document",  200),
    ("Document",  "main_personal_doc",            "Member document",   403),
    ("Task",      "task_id_list",                 "Task",              403),
    ("Milestone", "temp_milestone_on_temp_board", "Milestone",         403),
], ids=[
    "space-200",
    "space_doc-200",
    "project-200",
    "project_doc-200",
    "member_doc-403",
    "task-403",
    "milestone-403",
])
def test_get_history_project_only_access(
    request, main_space, kind, kind_id_fixture, entity, expected_status,
):
    """Project-only клиент: видит Space, Project и их документы, не видит бордовые сущности и Member doc."""
    client = request.getfixturevalue("client_with_access_only_in_project")
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    sees = "видит" if expected_status == 200 else "не видит"
    allure.dynamic.title(f"Клиент с доступом к Project: {sees} {entity} → {expected_status}")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}' ({entity}) от имени project_only client"):
        resp = client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step(f"Получаем {expected_status} ({'OK' if expected_status == 200 else 'Forbidden'})"):
        assert resp.status_code == expected_status, f"Ожидали {expected_status} ({'OK' if expected_status == 200 else 'Forbidden'}), получили: {short_resp(resp)}"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Personal doc: доступен только владельцу (main_client)
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Access matrix")
@pytest.mark.parametrize("client_fixture,expected_status", [
    ("main_client",    200),
    ("owner_client",   403),
    ("manager_client", 403),
    ("guest_client",   403),
], ids=[
    "owner_of_doc-200",
    "owner-403",
    "manager-403",
    "guest-403",
])
def test_get_history_personal_doc_access(
    request, main_space, client_fixture, expected_status,
):
    """Персональный документ доступен только владельцу (main_client), остальные получают 403."""
    client = request.getfixturevalue(client_fixture)
    kind_id = request.getfixturevalue("main_personal_doc")

    sees = "видит" if expected_status == 200 else "не видит"
    allure.dynamic.title(f"Персональный документ: {client_fixture} {sees} → {expected_status}")

    with allure.step(f"Отправляем POST /GetHistory: kind='Document' (Personal document) от имени {client_fixture}"):
        resp = client.post(
            path="/GetHistory",
            json={"kind": "Document", "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step(f"Получаем {expected_status} ({'OK' if expected_status == 200 else 'Forbidden'})"):
        assert resp.status_code == expected_status, f"Ожидали {expected_status} ({'OK' if expected_status == 200 else 'Forbidden'}), получили: {short_resp(resp)}"
