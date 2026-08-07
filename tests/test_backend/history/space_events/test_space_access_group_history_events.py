import uuid

import allure
import pytest

from test_backend.data.endpoints.access_group.access_group_endpoints import (
    create_access_group_endpoint,
    update_access_group_endpoint,
    remove_access_group_endpoint,
    set_access_group_member_endpoint,
    remove_access_group_member_endpoint,
)
from test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


def _create_group(client, space_id: str, name: str = None) -> tuple:
    """Вспомогательная функция: создаёт группу (Groups) и возвращает (group_id, name)."""
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
@allure.suite("Space events")
@allure.sub_suite("Access Group")
@allure.title("ACCESS_GROUP_CREATED — создание группы, проверка через GetHistory спейса")
def test_access_group_created_event(main_client, space_for_history):
    """
    Сценарий: создание группы (Groups) в спейсе.

    Шаги:
    1. Создаём группу (CreateAccessGroup)
    2. Проверяем через GetHistory что появилось событие ACCESS_GROUP_CREATED
    3. Проверяем data: groupId, name
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
@allure.suite("Space events")
@allure.sub_suite("Access Group")
@pytest.mark.parametrize("update_field, update_value", [
    ("name", "_at_group_renamed"),
    ("description", "updated description"),
], ids=["update_name", "update_description"])
def test_access_group_updated_event(main_client, space_for_history, update_field, update_value):
    """
    Сценарий: обновление имени или описания группы.

    Шаги:
    1. Создаём группу
    2. Обновляем поле (name или description) через UpdateAccessGroup
    3. Проверяем через GetHistory что появилось событие ACCESS_GROUP_UPDATED
    4. Проверяем data: groupId, name (актуальное имя после обновления)
    """
    allure.dynamic.title(f"ACCESS_GROUP_UPDATED — обновление {update_field} группы, проверка через GetHistory спейса")
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу"):
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
@allure.suite("Space events")
@allure.sub_suite("Access Group")
@allure.title("ACCESS_GROUP_REMOVED — удаление группы, проверка через GetHistory спейса")
def test_access_group_removed_event(main_client, space_for_history):
    """
    Сценарий: удаление группы из спейса.

    Шаги:
    1. Создаём группу
    2. Удаляем группу через RemoveAccessGroup
    3. Проверяем через GetHistory что появилось событие ACCESS_GROUP_REMOVED
    4. Проверяем data: groupId, name
    """
    space_id = space_for_history["space_id"]

    with allure.step("Создаём группу"):
        group_id, group_name = _create_group(main_client, space_id, name="_at_group_removed")

    with allure.step("Удаляем группу"):
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


@allure.parent_suite("History Service")
@allure.suite("Space events")
@allure.sub_suite("Access Group")
@allure.title("MEMBER_SET_ACCESS / MEMBER_REMOVE_ACCESS — добавление и удаление участника из группы, проверка через GetHistory спейса")
def test_member_set_and_remove_access_events(main_client, space_for_history, manager_in_space):
    """
    Сценарий: добавление и удаление участника из группы доступа.

    Шаги:
    1. Создаём группу доступа в спейсе
    2. Добавляем manager в группу (SetAccessGroupsMember)
       → проверяем через GetHistory событие MEMBER_SET_ACCESS
    3. Удаляем manager из группы (RemoveAccessGroupMember)
       → проверяем через GetHistory событие MEMBER_REMOVE_ACCESS
    """
    space_id = space_for_history["space_id"]
    member_id = manager_in_space["member_id"]

    with allure.step("1. Создаём группу доступа"):
        group_id, group_name = _create_group(main_client, space_id, name="_at_member_access")

    with allure.step("2. Добавляем manager в группу → ожидаем MEMBER_SET_ACCESS"):
        resp = main_client.post(**set_access_group_member_endpoint(
            space_id=space_id,
            member_id=member_id,
            access_group_id=group_id,
        ))
        assert resp.status_code == 200, f"Ошибка добавления в группу: {resp.text}"

    event_set = assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="MEMBER_SET_ACCESS",
        expected_data={
            "groupId": group_id,
            "groupName": group_name,
            "members": [member_id],
        },
        assert_unique=True,
    )

    with allure.step("Проверяем что data содержит только groupId, groupName, members"):
        expected_keys = {"groupId", "groupName", "members"}
        assert set(event_set["data"].keys()) == expected_keys, (
            f"Лишние поля в data: {set(event_set['data'].keys()) - expected_keys}"
        )

    with allure.step("3. Удаляем manager из группы → ожидаем MEMBER_REMOVE_ACCESS"):
        resp = main_client.post(**remove_access_group_member_endpoint(
            space_id=space_id,
            member_id=member_id,
            access_group_id=group_id,
        ))
        assert resp.status_code == 200, f"Ошибка удаления из группы: {resp.text}"

    event_remove = assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="MEMBER_REMOVE_ACCESS",
        expected_data={
            "groupId": group_id,
            "groupName": group_name,
            "members": [member_id],
        },
        assert_unique=True,
    )

    with allure.step("Проверяем что data содержит только groupId, groupName, members"):
        expected_keys = {"groupId", "groupName", "members"}
        assert set(event_remove["data"].keys()) == expected_keys, (
            f"Лишние поля в data: {set(event_remove['data'].keys()) - expected_keys}"
        )
