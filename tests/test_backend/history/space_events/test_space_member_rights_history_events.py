import uuid

import allure
import pytest

from config.settings import USERS
from test_backend.data.endpoints.Space.space_endpoints import get_spaces_endpoint
from test_backend.data.endpoints.access_group.aaccess_group_endpoints import (
    create_access_group_endpoint,
    set_access_group_member_endpoint,
    remove_access_group_member_endpoint,
)
from test_backend.data.endpoints.invite.invite_endpoint import (
    invite_to_space_endpoint,
    confirm_space_invite_endpoint,
)
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("MEMBER_SET_ACCESS → MEMBER_REMOVE_ACCESS events")
def test_member_set_and_remove_access_events(main_client, guest_client, space_for_history):
    """
    При добавлении участника в группу доступа → MEMBER_SET_ACCESS.
    При удалении участника из группы доступа → MEMBER_REMOVE_ACCESS.
    """
    space_id = space_for_history["space_id"]
    guest_email = USERS['guest']['email']
    guest_password = USERS['guest']['password']

    with allure.step("Приглашаем guest в space и он принимает инвайт"):
        ids_before = {
            m["_id"] for m in
            main_client.post(**get_space_members_endpoint(space_id=space_id)).json()["payload"]["members"]
        }

        invite_resp = main_client.post(**invite_to_space_endpoint(
            space_id=space_id,
            email=guest_email,
            space_access="Member",
        ))
        assert invite_resp.status_code == 200, f"Ошибка инвайта: {invite_resp.text}"

        spaces_resp = guest_client.post(**get_spaces_endpoint())
        assert spaces_resp.status_code == 200
        spaces = spaces_resp.json().get("payload", {}).get("spaces", [])
        target = next((s for s in spaces if s.get("_id") == space_id), None)
        assert target is not None, f"Space {space_id} не найден в инвайтах guest_client"

        confirm_resp = guest_client.post(**confirm_space_invite_endpoint(
            code=target["inviteCode"],
            full_name="guest",
            password=guest_password,
            termsAccepted=True,
        ))
        assert confirm_resp.status_code == 200, f"Ошибка подтверждения инвайта: {confirm_resp.text}"

        members_after = main_client.post(**get_space_members_endpoint(space_id=space_id)).json()["payload"]["members"]
        guest_member = next((m for m in members_after if m["_id"] not in ids_before), None)
        assert guest_member is not None, "guest не найден в списке участников после принятия инвайта"
        member_id = guest_member["_id"]

    with allure.step("Создаём группу доступа с правами Member на space"):
        group_name = f"rights_test_{uuid.uuid4().hex[:6]}"
        group_resp = main_client.post(**create_access_group_endpoint(
            space_id=space_id,
            name=group_name,
            description="group for member rights events test",
            space_accesses={space_id: "Member"},
        ))
        assert group_resp.status_code == 200, f"Ошибка создания группы: {group_resp.text}"
        group_id = group_resp.json()["payload"]["accessGroup"]["_id"]

    with allure.step("Добавляем guest в группу доступа → ожидаем MEMBER_SET_ACCESS"):
        set_resp = main_client.post(**set_access_group_member_endpoint(
            space_id=space_id,
            member_id=member_id,
            access_group_id=group_id,
        ))
        assert set_resp.status_code == 200, f"Ошибка добавления в группу: {set_resp.text}"

        assert_history_event_exists(
            client=main_client,
            space_id=space_id,
            kind="Space",
            kind_id=space_id,
            expected_event_key="MEMBER_SET_ACCESS",
        )

    with allure.step("Удаляем guest из группы доступа → ожидаем MEMBER_REMOVE_ACCESS"):
        remove_resp = main_client.post(**remove_access_group_member_endpoint(
            space_id=space_id,
            member_id=member_id,
            access_group_id=group_id,
        ))
        assert remove_resp.status_code == 200, f"Ошибка удаления из группы: {remove_resp.text}"

        assert_history_event_exists(
            client=main_client,
            space_id=space_id,
            kind="Space",
            kind_id=space_id,
            expected_event_key="MEMBER_REMOVE_ACCESS",
        )
