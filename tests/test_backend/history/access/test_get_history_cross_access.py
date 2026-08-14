import allure
import pytest

from core.response_utils import short_resp
from test_backend.data.endpoints.History.get_history_endpoint import get_history_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event
from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, delete_task_endpoint
from test_backend.data.endpoints.milestone.milestones_endpoints import create_milestone_endpoint, archive_milestone_endpoint

pytestmark = [pytest.mark.backend]


# ──────────────────────────────────────────────────────────────────────────────
# 1. Кросс-проект: project_client имеет доступ к main_project, но НЕ к temp_main_project_2
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Cross access: Cross project — прямой доступ → 403")
@pytest.mark.parametrize("kind,kind_id_fixture,entity", [
    ("Project",   "temp_main_project_2",                   "Кросс_проект_2"),
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
    но НЕ к temp_main_project_2. Все сущности project_2 должны вернуть 403 (Forbidden).
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(f"GetHistory: project_client → {entity} → 403 (Forbidden)")

    with allure.step(
        f"Отправляем POST /GetHistory: kind='{kind}' ({entity}) "
        f"от имени project_client который имеет доступ к main_project,но НЕ к temp_main_project_2"
    ):
        resp = client_with_access_only_in_project.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": kind_id},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 403 (Forbidden)"):
        assert resp.status_code == 403, f"Ожидали 403 (Forbidden), получили: {short_resp(resp)}"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Кросс-борд: member_client имеет доступ к main_project,
#    но НЕ к приватной борде (temp_board_in_main), созданной owner_client
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Cross access: Cross board — прямой доступ → 403")
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
    Задачи и майлстоуны на этой борде недоступны → 403 (Forbidden).
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    if isinstance(kind_id, list):
        kind_id = kind_id[0]

    allure.dynamic.title(
        f"GetHistory: member_client → {entity} → 403 (Forbidden)"
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

    with allure.step("Получаем 403 (Forbidden)"):
        assert resp.status_code == 403, f"Ожидали 403 (Forbidden), получили: {short_resp(resp)}"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Кросс-спейс: main_client имеет доступ к main_space,
#    но НЕ к foreign_space (созданному guest_client)
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Cross access: Cross space — прямой доступ → 403")
def test_get_history_no_access_to_other_space(main_client, main_space, foreign_space):
    """
    Кросс-спейс изоляция: main_client находится в main_space,
    но НЕ в foreign_space. Запрос истории foreign_space
    через свой Current-Space-Id не должен вернуть 200.
    """
    allure.dynamic.title("GetHistory: main_client → foreign_space → 403 (Forbidden)")

    with allure.step(
        f"Отправляем POST /GetHistory: kind='Space', kindId=foreign_space "
        f"от имени main_client с Current-Space-Id=main_space"
    ):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Space", "kindId": foreign_space},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 403 (Forbidden) — main_client не является участником foreign_space"):
        assert resp.status_code == 403, f"Ожидали 403 (Forbidden), получили: {short_resp(resp)}"


# ──────────────────────────────────────────────────────────────────────────────
# 4. Утечка событий: member_client имеет доступ к main_project,
#    но НЕ к приватной борде. События с приватной борды НЕ должны
#    попадать в Space/Project history для member_client.
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Cross access: Cross board history — утечка через Space/Project history")
@pytest.mark.xfail(
    reason="BUG: Space/Project history не фильтрует события по доступу к борде — "
           "member_client видит события с приватной борды",
    strict=True,
)
@pytest.mark.parametrize("kind, kind_id_fixture", [
    ("Space",   "main_space"),
    ("Project", "main_project"),
], ids=["Space_history", "Project_history"])
@pytest.mark.parametrize("entity", ["Task", "Milestone", "Board"], ids=["Task", "Milestone", "Board"])
def test_history_hides_private_board_events(
    request, owner_client, member_client, main_space, main_project,
    temp_board_in_main, kind, kind_id_fixture, entity,
):
    """
    member_client имеет доступ к main_project, но НЕ к temp_board_in_main.
    Создаём сущность (Task/Milestone) на приватной борде или используем
    существующую борду и проверяем:
    - owner видит событие в Space/Project history
    - member НЕ видит событие в Space/Project history
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    allure.dynamic.title(
        f"{kind} history: {entity} от приватной борды НЕ видны member_client"
    )

    entity_id = None
    cleanup = None

    if entity == "Task":
        entity_name = "Private board task for leakage test"
        with allure.step("Owner создаёт Task на приватной борде"):
            create_resp = owner_client.post(
                **create_task_endpoint(
                    space_id=main_space, board=temp_board_in_main, name=entity_name,
                )
            )
            assert create_resp.status_code == 200, f"Ошибка создания задачи: {short_resp(create_resp)}"
            entity_id = create_resp.json()["payload"]["task"]["_id"]
        expected_event_key = "TASK_CREATED"
        cleanup = lambda: owner_client.post(
            **delete_task_endpoint(space_id=main_space, task_id=entity_id)
        )

    elif entity == "Milestone":
        entity_name = "Private board milestone for leakage test"
        with allure.step("Owner создаёт Milestone на приватной борде"):
            create_resp = owner_client.post(
                **create_milestone_endpoint(
                    space_id=main_space, board=temp_board_in_main, name=entity_name,
                )
            )
            assert create_resp.status_code == 200, f"Ошибка создания майлстоуна: {short_resp(create_resp)}"
            entity_id = create_resp.json()["payload"]["milestone"]["_id"]
        expected_event_key = "MILESTONE_CREATED"
        cleanup = lambda: owner_client.post(
            **archive_milestone_endpoint(space_id=main_space, milestone_id=entity_id)
        )

    else:  # Board
        entity_id = temp_board_in_main
        entity_name = "_autotest_temp_board"
        expected_event_key = "BOARD_CREATED"

    try:
        if entity in ("Task", "Milestone"):
            with allure.step(f"Precondition: member_client НЕ имеет прямого доступа к {entity}"):
                pre_resp = member_client.post(
                    **get_history_endpoint(
                        space_id=main_space, kind=entity, kind_id=entity_id,
                    )
                )
                assert pre_resp.status_code == 403, (
                    f"Precondition failed: member_client имеет доступ к {entity} "
                    f"на приватной борде (ожидали 403, получили {pre_resp.status_code})"
                )

        with allure.step(f"Owner видит {expected_event_key} в {kind} history"):
            assert_get_history_event(
                client=owner_client,
                space_id=main_space,
                kind=kind,
                kind_id=kind_id,
                expected_event_key=expected_event_key,
                expected_data={"_id": entity_id, "name": entity_name},
            )

        with allure.step(f"Member запрашивает {kind} history"):
            resp = member_client.post(
                **get_history_endpoint(
                    space_id=main_space, kind=kind, kind_id=kind_id,
                )
            )
            assert resp.status_code == 200, f"Ожидали 200: {short_resp(resp)}"

        items = resp.json().get("payload", {}).get("items", [])

        with allure.step(f"Events с {entity}_id от приватной борды отсутствуют у member"):
            leaked = [
                item for item in items
                if item.get("data", {}).get("_id") == entity_id
            ]
            assert len(leaked) == 0, (
                f"Утечка: событие с {entity}_id={entity_id} видно member_client "
                f"в {kind} history, хотя доступа к борде нет.\n"
                f"Leaked events: {leaked}"
            )
    finally:
        if cleanup:
            with allure.step(f"Teardown: удаляем {entity}"):
                cleanup()


# ──────────────────────────────────────────────────────────────────────────────
# 5. Кросс-проект утечка: client_with_access_only_in_project имеет доступ
#    к main_project, но НЕ к temp_main_project_2. События из project_2
#    НЕ должны попадать в Space history.
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Cross access: Cross project history — утечка через Space history")
@pytest.mark.parametrize("entity", [
    "Task",
    pytest.param("Milestone", marks=pytest.mark.xfail(
        reason="BUG: Space history не фильтрует MILESTONE_CREATED по доступу к проекту",
        strict=True,
    )),
    "Board",
    "Project",
], ids=["Task", "Milestone", "Board", "Project"])
def test_space_history_hides_other_project_events(
    owner_client, client_with_access_only_in_project, main_space,
    temp_main_project_2, temp_board_in_project_2, entity,
):
    """
    client_with_access_only_in_project имеет доступ к main_project,
    но НЕ к temp_main_project_2. Создаём сущность в project_2 и проверяем:
    - owner видит событие в Space history
    - project_client НЕ видит событие в Space history
    """
    allure.dynamic.title(
        f"Space history: {entity} из чужого проекта НЕ видны project_client"
    )

    entity_id = None
    cleanup = None

    if entity == "Task":
        entity_name = "Project_2 task for leakage test"
        with allure.step("Owner создаёт Task в project_2"):
            create_resp = owner_client.post(
                **create_task_endpoint(
                    space_id=main_space, board=temp_board_in_project_2, name=entity_name,
                )
            )
            assert create_resp.status_code == 200, f"Ошибка создания задачи: {short_resp(create_resp)}"
            entity_id = create_resp.json()["payload"]["task"]["_id"]
        expected_event_key = "TASK_CREATED"
        cleanup = lambda: owner_client.post(
            **delete_task_endpoint(space_id=main_space, task_id=entity_id)
        )

    elif entity == "Milestone":
        entity_name = "Project_2 milestone for leakage test"
        with allure.step("Owner создаёт Milestone в project_2"):
            create_resp = owner_client.post(
                **create_milestone_endpoint(
                    space_id=main_space, board=temp_board_in_project_2, name=entity_name,
                )
            )
            assert create_resp.status_code == 200, f"Ошибка создания майлстоуна: {short_resp(create_resp)}"
            entity_id = create_resp.json()["payload"]["milestone"]["_id"]
        expected_event_key = "MILESTONE_CREATED"
        cleanup = lambda: owner_client.post(
            **archive_milestone_endpoint(space_id=main_space, milestone_id=entity_id)
        )

    elif entity == "Board":
        entity_id = temp_board_in_project_2
        entity_name = "_autotest_temp_board_project_2"
        expected_event_key = "BOARD_CREATED"

    else:  # Project
        entity_id = temp_main_project_2
        entity_name = "_temp_project_2"
        expected_event_key = "PROJECT_CREATED"

    try:
        if entity in ("Task", "Milestone", "Project"):
            check_kind = entity
            with allure.step(f"Precondition: project_client НЕ имеет прямого доступа к {entity}"):
                pre_resp = client_with_access_only_in_project.post(
                    **get_history_endpoint(
                        space_id=main_space, kind=check_kind, kind_id=entity_id,
                    )
                )
                assert pre_resp.status_code == 403, (
                    f"Precondition failed: project_client имеет доступ к {entity} "
                    f"в project_2 (ожидали 403, получили {pre_resp.status_code})"
                )

        with allure.step(f"Owner видит {expected_event_key} в Space history"):
            assert_get_history_event(
                client=owner_client,
                space_id=main_space,
                kind="Space",
                kind_id=main_space,
                expected_event_key=expected_event_key,
                expected_data={"_id": entity_id, "name": entity_name},
            )

        with allure.step("project_client запрашивает Space history"):
            resp = client_with_access_only_in_project.post(
                **get_history_endpoint(
                    space_id=main_space, kind="Space", kind_id=main_space,
                )
            )
            assert resp.status_code == 200, f"Ожидали 200: {short_resp(resp)}"

        items = resp.json().get("payload", {}).get("items", [])

        with allure.step(f"Events с {entity}_id из project_2 отсутствуют у project_client"):
            leaked = [
                item for item in items
                if item.get("data", {}).get("_id") == entity_id
            ]
            assert len(leaked) == 0, (
                f"Утечка: событие с {entity}_id={entity_id} видно project_client "
                f"в Space history, хотя доступа к project_2 нет.\n"
                f"Leaked events: {leaked}"
            )
    finally:
        if cleanup:
            with allure.step(f"Teardown: удаляем {entity}"):
                cleanup()
