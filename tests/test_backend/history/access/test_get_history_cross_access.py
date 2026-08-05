import allure
import pytest

pytestmark = [pytest.mark.backend]


# ──────────────────────────────────────────────────────────────────────────────
# 1. Кросс-проект: project_client имеет доступ к main_project, но НЕ к main_project_2
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Negative: GetHistory — кросс-проект")
@pytest.mark.parametrize("kind,kind_id_fixture,entity", [
    ("Project",   "main_project_2",                   "Проект"),
    ("Task",      "temp_task_in_project_2",            "Задача в проекте_2"),
    ("Milestone", "temp_milestone_in_project_2",       "Майлстоун в проекте_2"),
    ("Document",  "isolation_project_2_doc",           "Проджект-документ проекта_2"),
    ("Document",  "isolation_project_2_member_doc",    "Персональный проджект-документ_2"),
    ("Document",  "isolation_space_member_doc",        "Персональный спейс-документ"),
], ids=[
    "project_2-403",
    "task_in_project_2-403",
    "milestone_in_project_2-403",
    "project_2_doc-403",
    "project_2_member_doc-403",
    "space_member_doc-403",
])
def test_get_history_no_access_to_other_project(
    request, main_space, client_with_access_only_in_project,
    kind, kind_id_fixture, entity,
):
    """
    Кросс-проект изоляция: project_client имеет доступ к main_project,
    но НЕ к main_project_2. Все сущности project_2 должны вернуть 403.
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(f"GetHistory: project_client → {entity} → 403")

    with allure.step(
        f"Отправляем POST /GetHistory: kind='{kind}' ({entity}) "
        f"от имени project_client"
    ):
        resp = client_with_access_only_in_project.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 403"):
        assert resp.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# 2. Кросс-борд: member_client имеет доступ к main_project,
#    но НЕ к приватной борде (temp_board_in_main), созданной owner_client
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Negative: GetHistory — кросс-борд")
@pytest.mark.parametrize("kind,kind_id_fixture,entity", [
    ("Task",      "temp_task_on_temp_board",      "Задача на приватной борде"),
    ("Milestone", "temp_milestone_on_temp_board",  "Майлстоун на приватной борде"),
], ids=["task_private_board-403", "milestone_private_board-403"])
def test_get_history_no_access_to_other_board(
    request, main_space, member_client,
    kind, kind_id_fixture, entity,
):
    """
    Кросс-борд изоляция: member_client имеет доступ к main_project,
    но НЕ к приватной борде (temp_board_in_main), созданной owner_client.
    Задачи и майлстоуны на этой борде недоступны → 403.
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(
        f"GetHistory: member_client → {entity} → 403"
    )

    with allure.step(
        f"Отправляем POST /GetHistory: kind='{kind}' ({entity}) "
        f"от имени member_client"
    ):
        resp = member_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 403"):
        assert resp.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# 3. Кросс-спейс: main_client имеет доступ к main_space,
#    но НЕ к foreign_space (созданному guest_client)
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Negative: GetHistory — кросс-спейс")
def test_get_history_no_access_to_other_space(main_client, main_space, foreign_space):
    """
    Кросс-спейс изоляция: main_client находится в main_space,
    но НЕ в foreign_space. Запрос истории foreign_space
    через свой Current-Space-Id не должен вернуть 200.
    """
    allure.dynamic.title("GetHistory: main_client → foreign_space → не 200")

    with allure.step(
        f"Отправляем POST /GetHistory: kind='Space', kindId=foreign_space "
        f"от имени main_client с Current-Space-Id=main_space"
    ):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Space", "kindId": foreign_space},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 403 — main_client не является участником foreign_space"):
        assert resp.status_code == 403
