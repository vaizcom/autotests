import allure
import pytest

from config.generators import generate_email
from test_backend.data.endpoints.invite.assert_invite_payload import assert_invite_payload
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint, resend_invite_endpoint, \
    remove_invite_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Access Resend/Remove Invitations")
@allure.title("Проверка прав на Resend/Remove инвайта в Space клиентом: {client_fixture}")
@pytest.mark.parametrize(
    "client_fixture, expected_status",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 403),
        ("guest_client", 403),
    ]
)
def test_space_resend_and_remove_invite_access_by_role(request, space_with_members, owner_client, client_fixture, expected_status):
    """
    Проверка прав доступа к Resend/Remove Invite.
    """
    # 1. Получаем клиента с нужной ролью
    client = request.getfixturevalue(client_fixture)
    email = generate_email()

    # 2. Owner создает инвайт для теста
    with allure.step("Подготовка: Owner создает инвайт для теста"):
        invite_resp = owner_client.post(
            **invite_to_space_endpoint(space_id=space_with_members, email=email, space_access="Member"))
        invite_id = invite_resp.json().get("payload", {}).get("invite", {}).get("_id")

    # 3. Отправляем запрос от имени этого клиента
    with allure.step(
            f"Попытка повторной отправки инвайта клиентом {client_fixture}. Ожидаемый статус: {expected_status}"):
        response = client.post(**resend_invite_endpoint(
            space_id=space_with_members,
            member_id=invite_id
        ))

        # 4. Проверяем, что сервер ответил ожидаемым статус-кодом
        assert response.status_code == expected_status, (
            f"Права доступа нарушены! Ожидался статус {expected_status}, получен {response.status_code}. Ответ: {response.text}"
        )
        if expected_status == 200:
            response = response.json()
            assert response.get("type", {}) == 'ResendInvite'
            assert response.get("payload").get("email") == email
            assert response.get("payload").get("sent") == True

    # 5. Очистка: удаляем созданный инвайт
    with allure.step(f"Попытка удаления инвайта клиентом {client_fixture}. Ожидаемый статус: {expected_status}"):
        response = client.post(**remove_invite_endpoint(space_id=space_with_members, member_id=invite_id))

        # 6. Проверяем, что сервер ответил ожидаемым статус-кодом
        assert response.status_code == expected_status, (
            f"Права доступа нарушены! Ожидался статус {expected_status}, получен {response.status_code}. Ответ: {response.text}"
        )
        if expected_status == 200:
            payload = response.json().get("payload", {}).get("invite", {})
            with allure.step("Валидация тела ответа"):
                assert_invite_payload(
                    invite=payload,
                    space_id=space_with_members,
                    email=email
                )