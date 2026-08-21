"""
Отзыв и возврат доступа к борде: проверка что фильтрация истории
реагирует на изменение прав в реальном времени.

Доступ был → события видны → доступ забрали → не видны → вернули → видны.
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
from test_backend.data.endpoints.History.history_utils import (
    assert_get_history_event, assert_get_history_no_event,
)
from test_backend.data.endpoints.Task.task_endpoints import (
    create_task_endpoint, delete_task_endpoint,
)

pytestmark = [pytest.mark.backend]


def _create_task(client, space_id, board_id, name):
    resp = client.post(**create_task_endpoint(space_id=space_id, board=board_id, name=name))
    assert resp.status_code == 200, f"Ошибка создания задачи: {short_resp(resp)}"
    return resp.json()["payload"]["task"]["_id"]


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Динамическое изменение доступа — отзыв и возврат доступа")
def test_board_access_revoke_and_restore(
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
