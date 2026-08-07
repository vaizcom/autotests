import uuid

import allure
import pytest

from config.settings import USERS
from test_backend.data.endpoints.access_group.access_group_endpoints import (
    create_access_group_endpoint,
    update_access_group_endpoint,
    remove_access_group_endpoint,
    set_access_group_member_endpoint,
    remove_access_group_member_endpoint,
)
from test_backend.data.endpoints.invite.invite_endpoint import (
    invite_to_space_endpoint,
    confirm_space_invite_endpoint,
)
from test_backend.data.endpoints.Space.space_endpoints import get_spaces_endpoint
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
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
@allure.title("ACCESS_GROUP_CREATED event")
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
    allure.dynamic.title(f"ACCESS_GROUP_UPDATED event — обновление {update_field}")
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
@allure.title("ACCESS_GROUP_REMOVED event")
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
@allure.title("MEMBER_SET_ACCESS → MEMBER_REMOVE_ACCESS events")
def test_member_set_and_remove_access_events(main_client, manager_client, space_for_history):
    """
    Сценарий: добавление и удаление участника из группы.

    Шаги:
    1. Создаём группу в спейсе
    2. Приглашаем manager в спейс (если ещё не приглашён)
    3. Находим member_id manager'а в списке участников спейса
    4. Добавляем manager в группу доступа (SetAccessGroupsMember)
       → ожидаем событие MEMBER_SET_ACCESS в Space history
    5. Удаляем manager из группы доступа (RemoveAccessGroupMember)
       → ожидаем событие MEMBER_REMOVE_ACCESS в Space history
    """
    space_id = space_for_history["space_id"]
    manager_email = USERS["manager"]["email"]
    manager_password = USERS["manager"]["password"]

    with allure.step("1. Создаём группу доступа"):
        group_id, group_name = _create_group(main_client, space_id, name="_at_member_access")

    with allure.step("2. Приглашаем manager в спейс"):
        invite_resp = main_client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email=manager_email,
            space_access="Manager",
        ))
        if invite_resp.status_code == 200:
            spaces_resp = manager_client.post(**get_spaces_endpoint())
            assert spaces_resp.status_code == 200
            spaces = spaces_resp.json().get("payload", {}).get("spaces", [])
            target = next((s for s in spaces if s.get("_id") == space_id), None)
            assert target is not None, f"Space {space_id} не найден у manager"
            confirm_resp = manager_client.post(**confirm_space_invite_endpoint(
                code=target["inviteCode"],
                full_name="manager",
                password=manager_password,
                termsAccepted=True,
            ))
            assert confirm_resp.status_code == 200, f"Ошибка принятия инвайта: {confirm_resp.text}"

    with allure.step("3. Получаем member_id manager'а"):
        members_resp = main_client.post(**get_space_members_endpoint(space_id=space_id))
        assert members_resp.status_code == 200
        members = members_resp.json()["payload"]["members"]
        manager_member = next((m for m in members if m.get("email") == manager_email), None)
        assert manager_member is not None, f"Manager ({manager_email}) не найден в участниках"
        member_id = manager_member["_id"]

    with allure.step("4. Добавляем manager в группу → ожидаем MEMBER_SET_ACCESS"):
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

    with allure.step("5. Удаляем manager из группы → ожидаем MEMBER_REMOVE_ACCESS"):
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
