import uuid

import allure
import pytest

from test_backend.data.endpoints.access_group.access_group_endpoints import (
    create_access_group_endpoint,
    update_access_group_endpoint,
    update_access_group_rights_endpoint,
    remove_access_group_endpoint,
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
@allure.suite("Space History")
@allure.title("ACCESS_GROUP_CREATED event")
def test_access_group_created_event(main_client, space_for_history):
    """
    При создании группы доступа генерируется событие ACCESS_GROUP_CREATED.
    data содержит groupId и name.
    """
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу доступа"):
        group_id, group_name = _create_group(main_client, space_id, name="_at_group_created")

    event = assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="ACCESS_GROUP_CREATED",
        expected_data={"groupId": group_id, "name": group_name},
        assert_unique=True,
    )

    with allure.step("Проверяем что data содержит только groupId и name"):
        assert set(event["data"].keys()) == {"groupId", "name"}, (
            f"Лишние поля в data: {set(event['data'].keys()) - {'groupId', 'name'}}"
        )


@allure.parent_suite("History Service")
@allure.suite("Space History")
@pytest.mark.parametrize("update_field, update_value", [
    ("name", "_at_group_renamed"),
    ("description", "updated description"),
], ids=["update_name", "update_description"])
def test_access_group_updated_event(main_client, space_for_history, update_field, update_value):
    """
    При обновлении имени/описания группы доступа генерируется событие ACCESS_GROUP_UPDATED.
    data содержит groupId и name.
    """
    allure.dynamic.title(f"ACCESS_GROUP_UPDATED event — обновление {update_field}")
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу доступа"):
        group_id, group_name = _create_group(
            main_client, space_id, name=f"_at_upd_{update_field}",
        )

    with allure.step(f"Обновляем {update_field} группы"):
        resp = main_client.post(**update_access_group_endpoint(
            space_id=space_id,
            group_id=group_id,
            **{update_field: update_value},
        ))
        assert resp.status_code == 200, f"Ошибка обновления группы: {resp.text}"

    expected_name = update_value if update_field == "name" else group_name
    event = assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="ACCESS_GROUP_UPDATED",
        expected_data={"groupId": group_id, "name": expected_name},
        assert_unique=True,
    )

    with allure.step("Проверяем что data содержит только groupId и name"):
        assert set(event["data"].keys()) == {"groupId", "name"}, (
            f"Лишние поля в data: {set(event['data'].keys()) - {'groupId', 'name'}}"
        )


@allure.parent_suite("History Service")
@allure.suite("Space History")
@pytest.mark.parametrize("rights_kind", ["Space", "Project", "Board"],
                         ids=["rights_on_space", "rights_on_project", "rights_on_board"])
def test_access_group_rights_updated_event(
    main_client, space_for_history, project_for_history, board_for_history, rights_kind,
):
    """
    При обновлении прав группы доступа на сущность генерируется событие ACCESS_GROUP_RIGHTS_UPDATED.
    data содержит groupId, groupName, kind, kindName и level.
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


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("ACCESS_GROUP_REMOVED event")
def test_access_group_removed_event(main_client, space_for_history):
    """
    При удалении группы доступа генерируется событие ACCESS_GROUP_REMOVED.
    data содержит groupId и name.
    """
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу доступа"):
        group_id, group_name = _create_group(main_client, space_id, name="_at_group_removed")

    with allure.step("Удаляем группу доступа"):
        resp = main_client.post(**remove_access_group_endpoint(
            space_id=space_id,
            group_id=group_id,
        ))
        assert resp.status_code == 200, f"Ошибка удаления группы: {resp.text}"

    event = assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="ACCESS_GROUP_REMOVED",
        expected_data={"groupId": group_id, "name": group_name},
        assert_unique=True,
    )

    with allure.step("Проверяем что data содержит только groupId и name"):
        assert set(event["data"].keys()) == {"groupId", "name"}, (
            f"Лишние поля в data: {set(event['data'].keys()) - {'groupId', 'name'}}"
        )
