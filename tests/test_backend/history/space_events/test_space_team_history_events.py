import allure
import pytest

from config.settings import USERS
from test_backend.data.endpoints.invite.invite_endpoint import (
    invite_to_space_endpoint,
    confirm_space_invite_endpoint,
    decline_space_invite_endpoint,
    remove_invite_endpoint,
    deactivate_member_endpoint,
    reactivate_member_endpoint,
)
from test_backend.data.endpoints.Space.space_endpoints import get_spaces_endpoint
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("SPACE_INVITED → SPACE_INVITE_ACCEPTED → SPACE_USER_DEACTIVATED → SPACE_USER_REACTIVATED")
def test_space_invite_lifecycle_events(main_client, owner_client, space_for_history):
    """
    Полный жизненный цикл участника space:
    приглашение → принятие → деактивация → реактивация.
    """
    space_id = space_for_history["space_id"]
    owner_email = USERS['owner']['email']
    owner_password = USERS['owner']['password']

    with allure.step("1. Приглашаем owner в space → ожидаем SPACE_INVITED"):
        invite_resp = main_client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email=owner_email,
            space_access="Member",
        ))
        assert invite_resp.status_code == 200, f"Ошибка инвайта: {invite_resp.text}"

        assert_history_event_exists(
            client=main_client,
            space_id=space_id,
            kind="Space",
            kind_id=space_id,
            expected_event_key="SPACE_INVITED",
        )

    with allure.step("2. owner принимает инвайт → ожидаем SPACE_INVITE_ACCEPTED"):
        spaces_resp = owner_client.post(**get_spaces_endpoint())
        assert spaces_resp.status_code == 200
        spaces = spaces_resp.json().get("payload", {}).get("spaces", [])
        target = next((s for s in spaces if s.get("_id") == space_id), None)
        assert target is not None, f"Space {space_id} не найден в списке инвайтов owner_client"
        invite_code = target["inviteCode"]

        confirm_resp = owner_client.post(**confirm_space_invite_endpoint(
            code=invite_code,
            full_name="owner",
            password=owner_password,
            termsAccepted=True,
        ))
        assert confirm_resp.status_code == 200, f"Ошибка подтверждения инвайта: {confirm_resp.text}"

        assert_history_event_exists(
            client=main_client,
            space_id=space_id,
            kind="Space",
            kind_id=space_id,
            expected_event_key="SPACE_INVITE_ACCEPTED",
        )

    with allure.step("3. Получаем member_id owner в space"):
        members_resp = main_client.post(**get_space_members_endpoint(space_id=space_id))
        assert members_resp.status_code == 200
        members = members_resp.json()["payload"]["members"]
        owner_member = next((m for m in members if m.get("fullName") == "owner"), None)
        assert owner_member is not None, "owner не найден в списке участников space"
        member_id = owner_member["_id"]

    with allure.step("4. Деактивируем owner → ожидаем SPACE_USER_DEACTIVATED"):
        deactivate_resp = main_client.post(**deactivate_member_endpoint(
            space_id=space_id,
            member_id=member_id,
        ))
        assert deactivate_resp.status_code == 200, f"Ошибка деактивации: {deactivate_resp.text}"

        assert_history_event_exists(
            client=main_client,
            space_id=space_id,
            kind="Space",
            kind_id=space_id,
            expected_event_key="SPACE_USER_DEACTIVATED",
        )

    with allure.step("5. Реактивируем owner → ожидаем SPACE_USER_REACTIVATED"):
        reactivate_resp = main_client.post(**reactivate_member_endpoint(
            space_id=space_id,
            member_id=member_id,
        ))
        assert reactivate_resp.status_code == 200, f"Ошибка реактивации: {reactivate_resp.text}"

        assert_history_event_exists(
            client=main_client,
            space_id=space_id,
            kind="Space",
            kind_id=space_id,
            expected_event_key="SPACE_USER_REACTIVATED",
        )


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("SPACE_INVITE_REMOVED event")
def test_space_invite_removed_event(main_client, space_for_history):
    """
    При удалении инвайта до его принятия генерируется событие SPACE_INVITE_REMOVED.
    """
    space_id = space_for_history["space_id"]
    manager_email = USERS['manager']['email']

    with allure.step("Получаем список участников до приглашения"):
        members_resp = main_client.post(**get_space_members_endpoint(space_id=space_id))
        assert members_resp.status_code == 200
        ids_before = {m["_id"] for m in members_resp.json()["payload"]["members"]}

    with allure.step("Приглашаем manager в space"):
        invite_resp = main_client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email=manager_email,
            space_access="Member",
        ))
        assert invite_resp.status_code == 200, f"Ошибка инвайта: {invite_resp.text}"

    with allure.step("Получаем member_id приглашённого manager"):
        members_resp = main_client.post(**get_space_members_endpoint(space_id=space_id))
        assert members_resp.status_code == 200
        members_after = members_resp.json()["payload"]["members"]
        invited_member = next((m for m in members_after if m["_id"] not in ids_before), None)
        assert invited_member is not None, "Приглашённый участник не найден в GetSpaceMembers"
        member_id = invited_member["_id"]

    with allure.step("Удаляем инвайт → ожидаем SPACE_INVITE_REMOVED"):
        remove_resp = main_client.post(**remove_invite_endpoint(
            space_id=space_id,
            member_id=member_id,
        ))
        assert remove_resp.status_code == 200, f"Ошибка удаления инвайта: {remove_resp.text}"

        assert_history_event_exists(
            client=main_client,
            space_id=space_id,
            kind="Space",
            kind_id=space_id,
            expected_event_key="SPACE_INVITE_REMOVED",
        )


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("SPACE_INVITE_DECLINED event")
def test_space_invite_declined_event(main_client, member_client, space_for_history):
    """
    При отклонении инвайта приглашённым пользователем генерируется событие SPACE_INVITE_DECLINED.
    """
    space_id = space_for_history["space_id"]
    member_email = USERS['member']['email']

    with allure.step("Приглашаем member в space"):
        invite_resp = main_client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email=member_email,
            space_access="Member",
        ))
        assert invite_resp.status_code == 200, f"Ошибка инвайта: {invite_resp.text}"

    with allure.step("Получаем invite code от имени member_client"):
        spaces_resp = member_client.post(**get_spaces_endpoint())
        assert spaces_resp.status_code == 200
        spaces = spaces_resp.json().get("payload", {}).get("spaces", [])
        target = next((s for s in spaces if s.get("_id") == space_id), None)
        assert target is not None, f"Space {space_id} не найден в инвайтах member_client"
        invite_code = target["inviteCode"]

    with allure.step("member_client отклоняет инвайт → ожидаем SPACE_INVITE_DECLINED"):
        decline_resp = member_client.post(**decline_space_invite_endpoint(
            space_id=space_id,
            code=invite_code,
        ))
        assert decline_resp.status_code == 200, f"Ошибка отклонения инвайта: {decline_resp.text}"

        assert_history_event_exists(
            client=main_client,
            space_id=space_id,
            kind="Space",
            kind_id=space_id,
            expected_event_key="SPACE_INVITE_DECLINED",
        )
