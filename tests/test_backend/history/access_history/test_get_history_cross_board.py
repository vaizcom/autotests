"""
Cross-board: security-проверки доступа к истории приватной борды (APP-5921).

Условия: member_client имеет доступ к проекту, но НЕ к приватной борде.

Секция 1 — Фильтр boardIds с недоступной бордой → 403.
Секция 2 — События с приватной борды не видны в Space/Project history.
Секция 3 — Выдали доступ → видит события → забрали → не видит → вернули → видит.

Прямой 403 на Task/Milestone без доступа к борде покрыт в test_get_history_access_matrix.py.

Как бэкенд обрабатывает запрос GetHistory:
  1. Запрос пришёл (REST / WebSocket / Public API).
  2. Проверка доступа — есть ли у пользователя доступ к запрашиваемой сущности?
     Нет → 403, дальше не идём. Да → собираем список разрешённых борд/проектов.
     Если переданы фильтры (boardIds и т.д.) — проверяем что они доступны.
  3. Запрос в БД — MongoDB-фильтр уже содержит список разрешённых boardIds/projectIds,
     поэтому база возвращает только те события, которые пользователь может видеть.

Тип события (create/edit/archive/…) роли не играет — проверка доступа одна для всех,
поэтому достаточно одного события на сущность.
Подтверждено разработчиком (APP-5921, 2026-08-20).

Функциональность пользовательских фильтров (eventKeys, dateRange, memberIds, boardIds)
тестируется отдельно в tests/test_backend/history/filters/.
"""
import allure
import pytest

from core.response_utils import short_resp
from test_backend.data.endpoints.access_group.access_group_endpoints import (
    create_access_group_endpoint,
    update_access_group_rights_endpoint,
    set_access_group_member_endpoint,
    remove_access_group_member_endpoint,
    remove_access_group_endpoint,
)
from test_backend.data.endpoints.Board.board_endpoints import create_board_custom_field_endpoint
from test_backend.data.endpoints.History.get_history_endpoint import get_history_endpoint
from test_backend.data.endpoints.History.history_utils import (
    assert_get_history_event, assert_get_history_no_event,
)
from test_backend.data.endpoints.Task.task_endpoints import (
    create_task_endpoint, delete_task_endpoint, edit_task_custom_field_endpoint,
)
from test_backend.data.endpoints.milestone.milestones_endpoints import (
    create_milestone_endpoint, archive_milestone_endpoint,
)

pytestmark = [pytest.mark.backend]


# ── Хелперы: создание сущностей на приватной борде ──────────────────────────


def _create_task(client, space_id, board_id, name):
    resp = client.post(**create_task_endpoint(space_id=space_id, board=board_id, name=name))
    assert resp.status_code == 200, f"Ошибка создания задачи: {short_resp(resp)}"
    return resp.json()["payload"]["task"]["_id"]


def _create_milestone(client, space_id, board_id, project_id, name):
    resp = client.post(**create_milestone_endpoint(
        space_id=space_id, board=board_id, name=name, project=project_id,
    ))
    assert resp.status_code == 200, f"Ошибка создания майлстоуна: {short_resp(resp)}"
    return resp.json()["payload"]["milestone"]["_id"]


def _create_cf_event(client, space_id, board_id, task_id, cf_name):
    """Создаёт Text CF на борде, устанавливает значение на задаче. Возвращает (task_id, field_id)."""
    cf_resp = client.post(**create_board_custom_field_endpoint(
        board_id=board_id, space_id=space_id, name=cf_name, type="Text",
    ))
    assert cf_resp.status_code == 200, f"Ошибка создания CF: {short_resp(cf_resp)}"
    field_id = cf_resp.json()["payload"]["customField"]["_id"]

    edit_resp = client.post(**edit_task_custom_field_endpoint(
        space_id=space_id, task_id=task_id, field_id=field_id, value="secret value",
    ))
    assert edit_resp.status_code == 200, f"Ошибка установки CF: {short_resp(edit_resp)}"
    return field_id


# ──────────────────────────────────────────────────────────────────────────────
# 1. Фильтр boardIds с недоступной бордой → 403
# ──────────────────────────────────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Без доступа к борде — обход доступа через фильтр boardIds")
@pytest.mark.parametrize("kind, kind_id_fixture", [
    ("Space",   "main_space"),
    ("Project", "main_project"),
], ids=["Space_history", "Project_history"])
def test_cross_board_filter_bypass_denied(
    request, owner_client, member_client, main_space,
    temp_board_in_main, kind, kind_id_fixture,
):
    """
    Запрашиваем историю спейса/проекта и передаём в фильтре boardIds
    приватную борду → API не даёт «обойти» доступ через фильтр: 403.
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    allure.dynamic.title(
        f"[APP-5921] {kind} history: фильтр boardIds с приватной бордой → 403"
    )

    with allure.step("Участники: owner (полный доступ), member (проект — да, приватная борда — нет)"):
        pass

    with allure.step("Precondition: owner видит события борды"):
        assert_get_history_event(
            client=owner_client,
            space_id=main_space,
            kind=kind,
            kind_id=kind_id,
            expected_event_key="BOARD_CREATED",
            expected_data={"_id": temp_board_in_main},
        )

    with allure.step(f"member_client запрашивает {kind} history с boardIds=[приватная борда]"):
        resp = member_client.post(
            **get_history_endpoint(
                space_id=main_space,
                kind=kind,
                kind_id=kind_id,
                board_ids=[temp_board_in_main],
            )
        )

    with allure.step("Получаем 403 (Forbidden)"):
        assert resp.status_code == 403, f"Ожидали 403, получили: {short_resp(resp)}"


# ──────────────────────────────────────────────────────────────────────────────
# 2. События с приватной борды в Space/Project history
#    member_client не должен видеть эти события
# ──────────────────────────────────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Без доступа к борде — события в Space/Project history")
@pytest.mark.parametrize("kind, kind_id_fixture", [
    ("Space",   "main_space"),
    ("Project", "main_project"),
], ids=["Space_history", "Project_history"])
@pytest.mark.parametrize("entity", [
    "Task", "Milestone", "Board", "CustomField",
], ids=["Task", "Milestone", "Board", "CustomField"])
def test_cross_board_events_not_visible(
    request, owner_client, member_client, main_space, main_project,
    temp_board_in_main, kind, kind_id_fixture, entity,
):
    """
    Запрашиваем историю спейса/проекта (доступ есть) →
    в ответе не должно быть событий с приватной борды.
    Owner создаёт сущность → owner видит событие → member НЕ видит.
    """
    kind_id = request.getfixturevalue(kind_id_fixture)
    allure.dynamic.title(
        f"[APP-5921] {kind} history: событие {entity} с приватной борды не отображается"
    )

    with allure.step("Участники: owner (полный доступ), member (проект — да, приватная борда — нет)"):
        pass

    entity_id = None
    cleanup = None

    try:
        if entity == "Task":
            entity_name = "Private board task for access_history test"
            with allure.step("Owner создаёт Task на приватной борде"):
                entity_id = _create_task(owner_client, main_space, temp_board_in_main, entity_name)
            expected_key = "TASK_CREATED"
            expected_data = {"_id": entity_id, "name": entity_name}
            cleanup = lambda: owner_client.post(
                **delete_task_endpoint(space_id=main_space, task_id=entity_id)
            )

        elif entity == "Milestone":
            entity_name = "Private board milestone for access_history test"
            with allure.step("Owner создаёт Milestone на приватной борде"):
                entity_id = _create_milestone(
                    owner_client, main_space, temp_board_in_main, main_project, entity_name,
                )
            expected_key = "MILESTONE_CREATED"
            expected_data = {"_id": entity_id, "name": entity_name}
            cleanup = lambda: owner_client.post(
                **archive_milestone_endpoint(space_id=main_space, milestone_id=entity_id)
            )

        elif entity == "Board":
            entity_id = temp_board_in_main
            expected_key = "BOARD_CREATED"
            expected_data = {"_id": entity_id}

        else:  # CustomField
            entity_name = "CF access_history test task"
            with allure.step("Owner создаёт задачу и CF-событие на приватной борде"):
                entity_id = _create_task(owner_client, main_space, temp_board_in_main, entity_name)
                field_id = _create_cf_event(
                    owner_client, main_space, temp_board_in_main, entity_id,
                    cf_name=f"cf_access_{kind.lower()}",
                )
            expected_key = "CUSTOM_FIELD_CHANGED"
            expected_data = {"_id": entity_id, "fieldId": field_id}
            cleanup = lambda: owner_client.post(
                **delete_task_endpoint(space_id=main_space, task_id=entity_id)
            )

        if entity in ("Task", "Milestone"):
            with allure.step(f"Precondition: member_client НЕ имеет прямого доступа к {entity}"):
                pre_resp = member_client.post(
                    **get_history_endpoint(space_id=main_space, kind=entity, kind_id=entity_id)
                )
                assert pre_resp.status_code == 403, (
                    f"Precondition failed: member_client имеет доступ к {entity} "
                    f"на приватной борде (ожидали 403, получили {pre_resp.status_code})"
                )

        with allure.step(f"Owner видит {expected_key} в {kind} history"):
            assert_get_history_event(
                client=owner_client,
                space_id=main_space,
                kind=kind,
                kind_id=kind_id,
                expected_event_key=expected_key,
                expected_data=expected_data,
            )

        with allure.step(f"member_client запрашивает {kind} history"):
            resp = member_client.post(
                **get_history_endpoint(space_id=main_space, kind=kind, kind_id=kind_id)
            )
            assert resp.status_code == 200, f"Ожидали 200: {short_resp(resp)}"

        items = resp.json().get("payload", {}).get("items", [])

        with allure.step(f"{expected_key} от приватной борды отсутствует у member_client"):
            leaked = [
                item for item in items
                if item.get("data", {}).get("_id") == entity_id
                and item.get("key") == expected_key
            ]
            assert len(leaked) == 0, (
                f"Утечка: {expected_key} с entity_id={entity_id} видно member_client "
                f"в {kind} history, хотя доступа к борде нет.\n"
                f"Leaked events: {leaked}"
            )
    finally:
        if cleanup:
            with allure.step(f"Teardown: удаляем {entity}"):
                cleanup()


# ──────────────────────────────────────────────────────────────────────────────
# 3. Отзыв и возврат доступа к борде
#    Доступ был → события видны → доступ забрали → не видны → вернули → видны
# ──────────────────────────────────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Без доступа к борде — отзыв и возврат доступа")
def test_cross_board_access_revoke_and_restore(
    owner_client, member_client, main_space, main_project,
    main_personal, temp_board_in_main,
):
    """
    Проверяем что проверка доступа работает в реальном времени:
    1. Выдаём доступ к борде → member видит события в Space history.
    2. Забираем доступ → member НЕ видит.
    3. Возвращаем доступ → member снова видит.

    Кэширование прав: при первом запросе пользователя бэкенд идёт в БД
    за его access-группами и кэширует результат на 5 минут. Следующие запросы
    берут права из кэша. Через 5 минут кэш протухает — при следующем запросе
    снова идёт в БД. Но если права изменились (добавили/убрали доступ к борде),
    кэш сбрасывается сразу — задержки быть не должно.
    Если тест флейкает — возможная причина в TTL кэша.
    """
    allure.dynamic.title(
        "[APP-5921] Space history: выдали доступ → видит, забрали → не видит, вернули → видит"
    )

    with allure.step("Участники: owner (полный доступ), member (проект — да, борда — доступ меняется в ходе теста)"):
        pass

    member_id = main_personal["member"][0]
    group_id = None
    task_id = None

    try:
        # ── Подготовка: создаём событие на приватной борде ──
        with allure.step("Owner создаёт задачу на приватной борде"):
            task_id = _create_task(
                owner_client, main_space, temp_board_in_main,
                "Task for revoke/restore test",
            )

        with allure.step("Owner видит TASK_CREATED в Space history"):
            assert_get_history_event(
                client=owner_client,
                space_id=main_space,
                kind="Space",
                kind_id=main_space,
                expected_event_key="TASK_CREATED",
                expected_data={"_id": task_id},
            )

        # ── 1. Выдаём доступ → member видит событие ──
        with allure.step("Owner создаёт access group с доступом к борде"):
            resp = owner_client.post(**create_access_group_endpoint(
                space_id=main_space,
                name="_autotest_revoke_restore",
                description="Temp group for revoke/restore test",
            ))
            assert resp.status_code == 200, f"Ошибка создания access group: {short_resp(resp)}"
            group_id = resp.json()["payload"]["accessGroup"]["_id"]

        with allure.step("Выдаём группе доступ Member к борде"):
            resp = owner_client.post(**update_access_group_rights_endpoint(
                space_id=main_space,
                group_id=group_id,
                kind="Board",
                kind_id=temp_board_in_main,
                level="Member",
            ))
            assert resp.status_code == 200, f"Ошибка выдачи прав: {short_resp(resp)}"

        with allure.step("Добавляем member в access group"):
            resp = owner_client.post(**set_access_group_member_endpoint(
                space_id=main_space,
                member_id=member_id,
                access_group_id=group_id,
            ))
            assert resp.status_code == 200, f"Ошибка добавления member: {short_resp(resp)}"

        with allure.step("member_client видит TASK_CREATED в Space history"):
            assert_get_history_event(
                client=member_client,
                space_id=main_space,
                kind="Space",
                kind_id=main_space,
                expected_event_key="TASK_CREATED",
                expected_data={"_id": task_id},
            )

        # ── 2. Отзываем доступ → member НЕ видит событие ──
        with allure.step("Убираем member из access group"):
            resp = owner_client.post(**remove_access_group_member_endpoint(
                space_id=main_space,
                member_id=member_id,
                access_group_id=group_id,
            ))
            assert resp.status_code == 200, f"Ошибка удаления member: {short_resp(resp)}"

        with allure.step("member_client НЕ видит TASK_CREATED в Space history"):
            assert_get_history_no_event(
                client=member_client,
                space_id=main_space,
                kind="Space",
                kind_id=main_space,
                expected_event_key="TASK_CREATED",
                expected_data={"_id": task_id},
            )

        # ── 3. Возвращаем доступ → member снова видит событие ──
        with allure.step("Возвращаем member в access group"):
            resp = owner_client.post(**set_access_group_member_endpoint(
                space_id=main_space,
                member_id=member_id,
                access_group_id=group_id,
            ))
            assert resp.status_code == 200, f"Ошибка возврата member: {short_resp(resp)}"

        with allure.step("member_client снова видит TASK_CREATED в Space history"):
            assert_get_history_event(
                client=member_client,
                space_id=main_space,
                kind="Space",
                kind_id=main_space,
                expected_event_key="TASK_CREATED",
                expected_data={"_id": task_id},
            )

    finally:
        with allure.step("Teardown: убираем member из группы и удаляем группу"):
            if group_id:
                owner_client.post(**remove_access_group_member_endpoint(
                    space_id=main_space,
                    member_id=member_id,
                    access_group_id=group_id,
                ))
                owner_client.post(**remove_access_group_endpoint(
                    space_id=main_space,
                    group_id=group_id,
                ))
            if task_id:
                owner_client.post(
                    **delete_task_endpoint(space_id=main_space, task_id=task_id)
                )
