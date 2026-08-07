import uuid

import allure
import pytest

from test_backend.data.endpoints.access_group.access_group_endpoints import (
    create_access_group_endpoint,
    update_access_group_rights_endpoint,
)
from test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


def _create_group(client, space_id: str, name: str = None) -> tuple:
    """Вспомогательная функция: создаёт группу доступа и возвращает (group_id, name)."""
    name = name or f"test_group_{uuid.uuid4().hex[:6]}"
    resp = client.post(**create_access_group_endpoint(
        space_id=space_id,
        name=name,
        description="history event test group",
    ))
    assert resp.status_code == 200, f"Ошибка создания группы: {resp.text}"
    group_id = resp.json()["payload"]["accessGroup"]["_id"]
    return group_id, name


@allure.parent_suite("History Service")
@allure.suite("Access Rights")
@pytest.mark.parametrize("rights_kind", ["Space", "Project", "Board"],
                         ids=["rights_on_space", "rights_on_project", "rights_on_board"])
def test_access_group_rights_updated_event(
    main_client, space_for_history, project_for_history, board_for_history, rights_kind,
):
    """
    Сценарий: изменение уровня доступа группы на сущность (Space/Project/Board).

    Шаги:
    1. Создаём группу доступа в спейсе
    2. Назначаем группе уровень Member на сущность через UpdateAccessGroupRights
    3. Проверяем через GetHistory что появилось событие ACCESS_GROUP_RIGHTS_UPDATED
    4. Проверяем data: groupId, groupName, kind, kindName, level
    """
    allure.dynamic.title(f"ACCESS_GROUP_RIGHTS_UPDATED event — rights on {rights_kind}")
    space_id = space_for_history["space_id"]

    kind_map = {
        "Space": (space_for_history["space_id"], space_for_history["name"]),
        "Project": (project_for_history["project_id"], project_for_history["name"]),
        "Board": (board_for_history["board_id"], board_for_history["name"]),
    }
    kind_id, kind_name = kind_map[rights_kind]

    with allure.step("Создаём группу доступа"):
        group_id, group_name = _create_group(
            main_client, space_id, name=f"_at_group_rights_{rights_kind.lower()}",
        )

    with allure.step(f"Обновляем права группы на {rights_kind} (уровень Member)"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id,
            group_id=group_id,
            kind=rights_kind,
            kind_id=kind_id,
            level="Member",
        ))
        assert resp.status_code == 200, f"Ошибка обновления прав группы: {resp.text}"

    event = assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="ACCESS_GROUP_RIGHTS_UPDATED",
        expected_data={
            "groupId": group_id,
            "groupName": group_name,
            "kind": rights_kind,
            "kindName": kind_name,
            "level": "Member",
        },
        assert_unique=True,
        check_self=False,
    )

    with allure.step("Проверяем что data содержит только groupId, groupName, kind, kindName, level"):
        expected_keys = {"groupId", "groupName", "kind", "kindName", "level"}
        assert set(event["data"].keys()) == expected_keys, (
            f"Лишние поля в data: {set(event['data'].keys()) - expected_keys}"
        )
