"""
Cross-project: security-проверки доступа к истории чужого проекта.

Условия: project_client имеет доступ к проекту_1, но НЕ к проекту_2.

События из проекта без доступа не видны в Space history.

Прямой 403 на сущности покрыт в test_get_history_access_matrix.py
и как precondition в тесте ниже.

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
from test_backend.data.endpoints.History.get_history_endpoint import get_history_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event
from test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    archive_document_endpoint,
)
from test_backend.data.endpoints.Task.task_endpoints import (
    create_task_endpoint, delete_task_endpoint,
)
from test_backend.data.endpoints.milestone.milestones_endpoints import (
    create_milestone_endpoint, archive_milestone_endpoint,
)

pytestmark = [pytest.mark.backend]


# ── Хелперы ─────────────────────────────────────────────────────────────────


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


# ──────────────────────────────────────────────────────────────────────────────
# События из проекта без доступа не видны в Space history
# ──────────────────────────────────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Без доступа к проекту — события в Space history")
@pytest.mark.parametrize("entity", [
    "Task", "Milestone", "Board", "Project", "Document",
], ids=["Task", "Milestone", "Board", "Project", "Document"])
def test_cross_project_events_not_visible_in_space_history(
    owner_client, client_with_access_only_in_project, main_space,
    temp_main_project_2, temp_board_in_project_2, entity,
):
    """
    project_client имеет доступ к main_project, но НЕ к temp_main_project_2.
    Owner создаёт сущность в project_2.
    Проверяем: owner видит событие в Space history, project_client — нет.
    """
    allure.dynamic.title(
        f"Space history: событие {entity} из проекта без доступа не отображается"
    )

    entity_id = None
    cleanup = None

    try:
        if entity == "Task":
            entity_name = "Project_2 task for access_history test"
            with allure.step("Owner создаёт Task в project_2"):
                entity_id = _create_task(
                    owner_client, main_space, temp_board_in_project_2, entity_name,
                )
            expected_key = "TASK_CREATED"
            expected_data = {"_id": entity_id, "name": entity_name}
            cleanup = lambda: owner_client.post(
                **delete_task_endpoint(space_id=main_space, task_id=entity_id)
            )

        elif entity == "Milestone":
            entity_name = "Project_2 milestone for access_history test"
            with allure.step("Owner создаёт Milestone в project_2"):
                entity_id = _create_milestone(
                    owner_client, main_space, temp_board_in_project_2,
                    temp_main_project_2, entity_name,
                )
            expected_key = "MILESTONE_CREATED"
            expected_data = {"_id": entity_id, "name": entity_name}
            cleanup = lambda: owner_client.post(
                **archive_milestone_endpoint(space_id=main_space, milestone_id=entity_id)
            )

        elif entity == "Board":
            entity_id = temp_board_in_project_2
            expected_key = "BOARD_CREATED"
            expected_data = {"_id": entity_id}

        elif entity == "Document":
            with allure.step("Owner создаёт Document в project_2"):
                resp = owner_client.post(**create_document_endpoint(
                    kind="Project", kind_id=temp_main_project_2, space_id=main_space,
                ))
                assert resp.status_code == 200, f"Ошибка создания документа: {short_resp(resp)}"
                entity_id = resp.json()["payload"]["document"]["_id"]
            expected_key = "DOCUMENT_CREATED"
            expected_data = {"_id": entity_id}
            cleanup = lambda: owner_client.post(**archive_document_endpoint(
                document_id=entity_id, space_id=main_space,
            ))

        else:  # Project
            entity_id = temp_main_project_2
            expected_key = "PROJECT_CREATED"
            expected_data = {"_id": entity_id}

        if entity in ("Task", "Milestone", "Project", "Document"):
            with allure.step(f"Precondition: project_client НЕ имеет прямого доступа к {entity}"):
                pre_resp = client_with_access_only_in_project.post(
                    **get_history_endpoint(space_id=main_space, kind=entity, kind_id=entity_id)
                )
                assert pre_resp.status_code == 403, (
                    f"Precondition failed: project_client имеет доступ к {entity} "
                    f"в project_2 (ожидали 403, получили {pre_resp.status_code})"
                )

        with allure.step(f"Owner видит {expected_key} в Space history"):
            assert_get_history_event(
                client=owner_client,
                space_id=main_space,
                kind="Space",
                kind_id=main_space,
                expected_event_key=expected_key,
                expected_data=expected_data,
            )

        with allure.step("project_client запрашивает Space history"):
            resp = client_with_access_only_in_project.post(
                **get_history_endpoint(space_id=main_space, kind="Space", kind_id=main_space)
            )
            assert resp.status_code == 200, f"Ожидали 200: {short_resp(resp)}"

        items = resp.json().get("payload", {}).get("items", [])

        with allure.step(f"{expected_key} из project_2 отсутствует у project_client"):
            leaked = [
                item for item in items
                if item.get("data", {}).get("_id") == entity_id
                and item.get("key") == expected_key
            ]
            assert len(leaked) == 0, (
                f"Утечка: {expected_key} с entity_id={entity_id} видно project_client "
                f"в Space history, хотя доступа к project_2 нет.\n"
                f"Leaked events: {leaked}"
            )
    finally:
        if cleanup:
            with allure.step(f"Teardown: удаляем {entity}"):
                cleanup()
