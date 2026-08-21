"""
Динамическое изменение доступа: проверка что фильтрация истории
реагирует на изменение прав в реальном времени.

Выдали доступ → события видны → забрали → не видны → вернули → видны.

Доступ управляется через UpdateAccessGroupRights на персональной
selfAccessGroup member (у каждого участника спейса своя группа).
level="Member" — выдать, level="NoAccess" — забрать.

Покрыты два уровня:
  - Борда: member получает/теряет доступ к приватной борде (temp_board_in_main).
  - Проект: member получает/теряет доступ к project_2 (temp_main_project_2).
"""
import allure
import pytest

from core.response_utils import short_resp
from test_backend.data.endpoints.access_group.access_group_endpoints import (
    update_access_group_rights_endpoint,
)
from test_backend.data.endpoints.History.history_utils import (
    assert_get_history_event, assert_get_history_no_event,
)

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Динамическое изменение доступа к борде — отзыв и возврат")
def test_board_access_revoke_and_restore(
    owner_client, member_client, main_space,
    temp_board_in_main, temp_task_on_private_board, member_access_group_id,
):
    """
    Проверяем что фильтрация Space history реагирует на изменение доступа к борде:
    1. Выдаём доступ к борде → member видит TASK_CREATED в Space history.
    2. Забираем доступ → member НЕ видит.
    3. Возвращаем доступ → member снова видит.

    Событие TASK_CREATED создаётся один раз (фикстура temp_task_on_private_board)
    и остаётся в БД навсегда. Тест не создаёт новых событий на каждом шаге —
    меняется только видимость: бэкенд при каждом GetHistory фильтрует события
    по текущим правам пользователя (MongoDB-фильтр по разрешённым boardIds).

    Кэширование прав: бэкенд кэширует access-группы на 5 минут,
    но при изменении прав кэш сбрасывается сразу.
    Если тест флейкает — возможная причина в TTL кэша.
    """
    task_id = temp_task_on_private_board

    allure.dynamic.title(
        "[APP-5921] Space history (борда): выдали доступ → видит, забрали → не видит, вернули → видит"
    )

    with allure.step("Участники: owner (полный доступ), member (проект — да, борда — доступ меняется в ходе теста)"):
        pass

    try:
        # ── 1. Выдаём доступ к борде → member видит событие ──
        with allure.step("Выдаём member доступ Member к борде"):
            resp = owner_client.post(**update_access_group_rights_endpoint(
                space_id=main_space, group_id=member_access_group_id,
                kind="Board", kind_id=temp_board_in_main, level="Member",
            ))
            assert resp.status_code == 200, f"Ошибка выдачи прав: {short_resp(resp)}"

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
        with allure.step("Убираем у member доступ к борде (NoAccess)"):
            resp = owner_client.post(**update_access_group_rights_endpoint(
                space_id=main_space, group_id=member_access_group_id,
                kind="Board", kind_id=temp_board_in_main, level="NoAccess",
            ))
            assert resp.status_code == 200, f"Ошибка отзыва прав: {short_resp(resp)}"

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
        with allure.step("Возвращаем member доступ Member к борде"):
            resp = owner_client.post(**update_access_group_rights_endpoint(
                space_id=main_space, group_id=member_access_group_id,
                kind="Board", kind_id=temp_board_in_main, level="Member",
            ))
            assert resp.status_code == 200, f"Ошибка возврата прав: {short_resp(resp)}"

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
        with allure.step("Teardown: убираем доступ к борде (NoAccess)"):
            owner_client.post(**update_access_group_rights_endpoint(
                space_id=main_space, group_id=member_access_group_id,
                kind="Board", kind_id=temp_board_in_main, level="NoAccess",
            ))


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Динамическое изменение доступа к проекту — отзыв и возврат")
def test_project_access_revoke_and_restore(
    owner_client, member_client, main_space,
    temp_main_project_2, member_access_group_id,
):
    """
    Проверяем что фильтрация Space history реагирует на изменение доступа к проекту:
    1. Выдаём доступ к project_2 → member видит PROJECT_CREATED в Space history.
    2. Забираем доступ → member НЕ видит.
    3. Возвращаем доступ → member снова видит.

    Событие PROJECT_CREATED создаётся при создании проекта (фикстура temp_main_project_2)
    и остаётся в БД навсегда. Тест не создаёт новых событий на каждом шаге —
    меняется только видимость: бэкенд при каждом GetHistory фильтрует события
    по текущим правам пользователя (MongoDB-фильтр по разрешённым projectIds).

    Используем PROJECT_CREATED, а не TASK_CREATED,
    потому что доступ к проекту не даёт доступ к бордам и их сущностям.
    """
    allure.dynamic.title(
        "Space history (проект): выдали доступ → видит, забрали → не видит, вернули → видит"
    )

    with allure.step("Участники: owner (полный доступ), member (main_project — да, project_2 — доступ меняется в ходе теста)"):
        pass

    try:
        # ── 1. Выдаём доступ к project_2 → member видит событие ──
        with allure.step("Выдаём member доступ Member к project_2"):
            resp = owner_client.post(**update_access_group_rights_endpoint(
                space_id=main_space, group_id=member_access_group_id,
                kind="Project", kind_id=temp_main_project_2, level="Member",
            ))
            assert resp.status_code == 200, f"Ошибка выдачи прав: {short_resp(resp)}"

        with allure.step("member_client видит PROJECT_CREATED в Space history"):
            assert_get_history_event(
                client=member_client,
                space_id=main_space,
                kind="Space",
                kind_id=main_space,
                expected_event_key="PROJECT_CREATED",
                expected_data={"_id": temp_main_project_2},
            )

        # ── 2. Отзываем доступ → member НЕ видит событие ──
        with allure.step("Убираем у member доступ к project_2 (NoAccess)"):
            resp = owner_client.post(**update_access_group_rights_endpoint(
                space_id=main_space, group_id=member_access_group_id,
                kind="Project", kind_id=temp_main_project_2, level="NoAccess",
            ))
            assert resp.status_code == 200, f"Ошибка отзыва прав: {short_resp(resp)}"

        with allure.step("member_client НЕ видит PROJECT_CREATED в Space history"):
            assert_get_history_no_event(
                client=member_client,
                space_id=main_space,
                kind="Space",
                kind_id=main_space,
                expected_event_key="PROJECT_CREATED",
                expected_data={"_id": temp_main_project_2},
            )

        # ── 3. Возвращаем доступ → member снова видит событие ──
        with allure.step("Возвращаем member доступ Member к project_2"):
            resp = owner_client.post(**update_access_group_rights_endpoint(
                space_id=main_space, group_id=member_access_group_id,
                kind="Project", kind_id=temp_main_project_2, level="Member",
            ))
            assert resp.status_code == 200, f"Ошибка возврата прав: {short_resp(resp)}"

        with allure.step("member_client снова видит PROJECT_CREATED в Space history"):
            assert_get_history_event(
                client=member_client,
                space_id=main_space,
                kind="Space",
                kind_id=main_space,
                expected_event_key="PROJECT_CREATED",
                expected_data={"_id": temp_main_project_2},
            )

    finally:
        with allure.step("Teardown: убираем доступ к project_2 (NoAccess)"):
            owner_client.post(**update_access_group_rights_endpoint(
                space_id=main_space, group_id=member_access_group_id,
                kind="Project", kind_id=temp_main_project_2, level="NoAccess",
            ))
