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
        group_id, group_name = _create_group(main_client, space_id)

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


ACCESS_GROUP_UPDATE_CASES = [
    pytest.param(
        {"name": f"updated_name_{uuid.uuid4().hex[:6]}"},
        "Обновление имени группы доступа",
        id="update_name",
    ),
    pytest.param(
        {"description": "updated description"},
        "Обновление описания группы доступа",
        id="update_description",
    ),
]


@allure.parent_suite("History Service")
@allure.suite("Space History")
@pytest.mark.parametrize("update_kwargs,title", ACCESS_GROUP_UPDATE_CASES)
def test_access_group_updated_event(main_client, space_for_history, update_kwargs, title):
    """
    При обновлении имени/описания группы доступа генерируется событие ACCESS_GROUP_UPDATED.
    data содержит groupId и name.
    """
    allure.dynamic.title(title)
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу доступа"):
        group_id, group_name = _create_group(main_client, space_id)

    with allure.step(f"Обновляем группу: {list(update_kwargs.keys())}"):
        resp = main_client.post(**update_access_group_endpoint(
            space_id=space_id,
            group_id=group_id,
            **update_kwargs,
        ))
        assert resp.status_code == 200, f"Ошибка обновления группы: {resp.text}"

    expected_name = update_kwargs.get("name", group_name)
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
@allure.title("ACCESS_GROUP_RIGHTS_UPDATED event")
def test_access_group_rights_updated_event(main_client, space_for_history):
    """
    При обновлении прав группы доступа генерируется событие ACCESS_GROUP_RIGHTS_UPDATED.
    data содержит groupId, groupName, kind, kindName и level.
    """
    space_id = space_for_history["space_id"]
    space_name = space_for_history["name"]

    with allure.step("Создаём группу доступа"):
        group_id, group_name = _create_group(main_client, space_id)

    with allure.step("Обновляем права группы на Space (уровень Member)"):
        resp = main_client.post(**update_access_group_rights_endpoint(
            space_id=space_id,
            group_id=group_id,
            kind="Space",
            kind_id=space_id,
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
            "kind": "Space",
            "kindName": space_name,
            "level": "Member",
        },
        assert_unique=True,
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
        group_id, group_name = _create_group(main_client, space_id)

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
