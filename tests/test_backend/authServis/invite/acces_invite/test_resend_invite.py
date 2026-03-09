import allure
import pytest

from config.generators import generate_email
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint, resend_invite_endpoint, \
    remove_invite_endpoint


@pytest.mark.parametrize(
    "client_fixture, expected_status",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 403),
        ("guest_client", 403),
    ]
)
def test_space_resend_invite_access_by_role(request, space_with_members, owner_client, client_fixture, expected_status):
    """
    Проверка прав доступа к ResendInvite.
    """
    pass
    client = request.getfixturevalue(client_fixture)
    email = generate_email()

    # Owner создает инвайт для теста
    invite_resp = owner_client.post(
        **invite_to_space_endpoint(space_id=space_with_members, email=email, space_access="Member"))

    invite_id = invite_resp.json().get("payload", {}).get("invite", {}).get("_id")

    with allure.step(
            f"Попытка повторной отправки инвайта клиентом {client_fixture}. Ожидаемый статус: {expected_status}"):
        response = client.post(**resend_invite_endpoint(
            space_id=space_with_members,
            member_id=invite_id
        ))

        assert response.status_code == expected_status, (
            f"Права доступа нарушены! Ожидался статус {expected_status}, получен {response.status_code}. Ответ: {response.text}"
        )

    owner_client.post(**remove_invite_endpoint(space_id=space_with_members, member_id=invite_id))