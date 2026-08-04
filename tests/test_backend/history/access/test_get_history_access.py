import allure
import pytest

pytestmark = [pytest.mark.backend]


# ──────────────────────────────────────────────────────────────────────────────
# 1. Пользователь не является участником спейса → 400 SpaceIdNotSpecified
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@pytest.mark.parametrize("kind,kind_id_fixture", [
    ("Space",     "main_space"),
    ("Project",   "main_project"),
    ("Task",      "task_id_list"),
    ("Document",  "main_space_doc"),
    ("Milestone", "temp_milestone_on_temp_board"),
], ids=["space", "project", "task", "document", "milestone"])
def test_get_history_user_not_in_space(request, foreign_client, main_space, kind, kind_id_fixture):
    """
    Пользователь без доступа к спейсу не может получить историю ни для одного kind.
    foreign_client не является участником main_space.
    Бек отклоняет на уровне проверки Current-Space-Id → 400 SpaceIdNotSpecified.
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(f"GetHistory: foreign_client запрашивает kind='{kind}' → 400 SpaceIdNotSpecified")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}' от имени foreign_client"):
        resp = foreign_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 400 SpaceIdNotSpecified"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SpaceIdNotSpecified"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Роли с доступом к спейсу → 200 для истории проекта
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@pytest.mark.parametrize("client_fixture", [
    "owner_client",
    "manager_client",
    "member_client",
    "guest_client",
], ids=["owner", "manager", "member", "guest"])
def test_get_history_roles_with_access(request, main_space, main_project, client_fixture):
    """Owner, Manager, Member, Guest имеют доступ к истории проекта."""
    client = request.getfixturevalue(client_fixture)

    allure.dynamic.title(f"GetHistory: {client_fixture} запрашивает историю проекта → 200")

    with allure.step(f"Отправляем POST /GetHistory: kind='Project' от имени {client_fixture}"):
        resp = client.post(
            path="/GetHistory",
            json={"kind": "Project", "kindId": main_project},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 200"):
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# 3. Матрица доступа по уровням иерархии: Space → Project → Board / Personal doc
#
# Уровень доступа клиента:
#   space-only   — в спейсе, но без доступа к проекту и борду
#   project-only — в спейсе и проекте, но без доступа к борду
#   personal doc — личный документ member_client, доступен только ему
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@pytest.mark.parametrize("client_fixture,kind,kind_id_fixture,entity,expected_status", [
    # space-only: видит Space и спейс-документы, не видит Project и ниже (включая Task, Milestone, Member doc)
    ("client_with_access_only_in_space", "Space",     "main_space",                   "Space",             200),
    ("client_with_access_only_in_space", "Document",  "main_space_doc",               "Space document",    200),
    ("client_with_access_only_in_space", "Project",   "main_project",                 "Project",           403),
    ("client_with_access_only_in_space", "Document",  "main_project_doc",             "Project document",  403),
    ("client_with_access_only_in_space", "Document",  "main_personal_doc",            "Member document",   403),
    ("client_with_access_only_in_space", "Task",      "task_id_list",                 "Task",              403),
    ("client_with_access_only_in_space", "Milestone", "temp_milestone_on_temp_board", "Milestone",         403),
    # project-only: видит Space, Project и их документы, не видит бордовые сущности и Member doc
    ("client_with_access_only_in_project", "Space",     "main_space",                   "Space",             200),
    ("client_with_access_only_in_project", "Document",  "main_space_doc",               "Space document",    200),
    ("client_with_access_only_in_project", "Project",   "main_project",                 "Project",           200),
    ("client_with_access_only_in_project", "Document",  "main_project_doc",             "Project document",  200),
    ("client_with_access_only_in_project", "Document",  "main_personal_doc",            "Member document",   403),
    ("client_with_access_only_in_project", "Task",      "task_id_list",                 "Task",              403),
    ("client_with_access_only_in_project", "Milestone", "temp_milestone_on_temp_board", "Milestone",         403),
    # personal doc: доступен только владельцу (main_client)
    ("main_client",    "Document", "main_personal_doc", "Personal document", 200),
    ("owner_client",   "Document", "main_personal_doc", "Personal document", 403),
    ("manager_client", "Document", "main_personal_doc", "Personal document", 403),
    ("guest_client",   "Document", "main_personal_doc", "Personal document", 403),
], ids=[
    "space_only-space-200",
    "space_only-space_doc-200",
    "space_only-project-403",
    "space_only-project_doc-403",
    "space_only-member_doc-403",
    "space_only-task-403",
    "space_only-milestone-403",
    "project_only-space-200",
    "project_only-space_doc-200",
    "project_only-project-200",
    "project_only-project_doc-200",
    "project_only-member_doc-403",
    "project_only-task-403",
    "project_only-milestone-403",
    "main-personal_doc-200",
    "owner-personal_doc-403",
    "manager-personal_doc-403",
    "guest-personal_doc-403",
])
def test_get_history_access_matrix(
    request, main_space, client_fixture, kind, kind_id_fixture, entity, expected_status
):
    """Матрица доступа: проверяем что GetHistory соблюдает иерархию Space → Project → Board → Personal."""
    client = request.getfixturevalue(client_fixture)
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(f"GetHistory: {client_fixture}, {entity} → {expected_status}")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}' ({entity}) от имени {client_fixture}"):
        resp = client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step(f"Получаем {expected_status}"):
        assert resp.status_code == expected_status
