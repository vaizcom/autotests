import allure
import pytest
from test_backend.data.endpoints.Space.space_endpoints import get_spaces_endpoint
from test_backend.data.endpoints.invite.invite_endpoint import (
    invite_to_space_endpoint,
    confirm_space_invite_endpoint
)
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from config import settings
pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Confirm Space Invite")
@allure.title("Успешное подтверждение инвайта новым пользователем")
def test_confirm_space_invite_success(main_client, temp_space, member_client):
    """
    Проверка успешного подтверждения приглашения в пространство.
    """

    member_email = settings.USERS['member']['email']
    member_password = settings.USERS['member']['password']
    full_name = "Confirmed User"

    with allure.step("Owner приглашает member_client в пространство"):
        invite_resp = main_client.post(**invite_to_space_endpoint(
            space_id=temp_space,
            email=member_email,
            space_access="Member"
        ))
        assert invite_resp.status_code == 200, f"Ошибка приглашения: {invite_resp.text}"
        resp = invite_resp.json()
        assert resp.get('payload', {}).get('invite', {}).get('status') == "Invited"

        with allure.step("Проверка статуса пользователя в списке участников (должен быть Invited)"):
            response = main_client.post(**get_space_members_endpoint(
                space_id=temp_space
            ))
            assert response.status_code == 200
            resp = response.json().get('payload').get('members')
            target_status = next((s for s in resp if s.get('email') == member_email), None)
            assert target_status is not None, "Приглашенный пользователь не найден в списке участников"
            assert target_status.get('status') == "Invited"


    with allure.step("Получение кода приглашения (inviteCode)"):
        spaces_resp = member_client.post(**get_spaces_endpoint())
        assert spaces_resp.status_code == 200, f"Ошибка получения спейсов: {spaces_resp.text}"

        spaces = spaces_resp.json().get('payload', {}).get('spaces', [])
        target_space = next((s for s in spaces if s.get('_id') == temp_space), None)
        assert target_space, "Пространство не найдено в списке спейсов member_client"

        invite_code = target_space.get('inviteCode')
        assert invite_code, "inviteCode отсутствует в ответе"
        assert target_space.get("isForeign") is True, "Флаг isForeign должен быть True"

    with allure.step("Подтверждение инвайта через ConfirmSpaceInvite приглашенным пользователем"):
        confirm_resp = member_client.post(**confirm_space_invite_endpoint(
            code=invite_code,
            full_name=full_name,
            password=member_password,
            termsAccepted=True
        ))
        assert confirm_resp.status_code == 200, f"Ошибка подтверждения: {confirm_resp.text}"

        payload = confirm_resp.json().get("payload", {})
        assert payload.get("alreadyAccepted") is False, "Флаг alreadyAccepted должен быть False"
        assert payload.get("spaceId") == temp_space, "Неверный spaceId в ответе"
        assert payload.get("termsAccepted") is True, "Флаг termsAccepted должен быть True"
        assert "token" not in payload, "В ответе присутствует токен авторизации"
        assert payload.get("hasPassword") is True, "Флаг hasPassword должен быть True"

        with allure.step("Проверка статуса пользователя в списке участников (должен быть Active)"):
            response = main_client.post(**get_space_members_endpoint(
                space_id=temp_space
            ))
            assert response.status_code == 200
            resp = response.json().get('payload').get('members')
            target_status = next((s for s in resp if s.get('email') == member_email), None)
            assert target_status is not None, "Приглашенный пользователь не найден в списке участников"
            assert target_status.get('status') == "Active"

# инвайт пользователя которого нет в базе. подтверждение через отправку кода = tokenHash, который нужно взять из монго бд: confirmtokens.({"payload.email": "test+1@test.com"})
# также учесть инвайт в space_id_module, потому что в temp_space закончилось кол-во инвайтов на фри тарифе = 10

@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Confirm Space Invite")
@allure.title("Успешное подтверждение инвайта пользователя, которого нет в базе")
def test_confirm_space_invite_new_user(owner_client, space_id_module, db):
    """
    Проверка успешного приглашения и подтверждения для пользователя,
    которого еще нет в базе данных.
    """

    new_user_email = "invite_new_user@autotest.com"
    new_user_password = "123456"
    full_name = "Brand New User"

    with allure.step("Owner приглашает нового пользователя в пространство (space_id_module)"):
        invite_resp = owner_client.post(**invite_to_space_endpoint(
            space_id=space_id_module,
            email=new_user_email,
            space_access="Member"
        ))
        assert invite_resp.status_code == 200, f"Ошибка приглашения: {invite_resp.text}"
        resp = invite_resp.json()
        assert resp.get('payload', {}).get('invite', {}).get('status') == "Invited"

    with allure.step("Ожидание и получение tokenHash (кода приглашения) из MongoDB"):

        token_doc = db.confirmtokens.find_one({"payload.email": new_user_email})
        assert token_doc is not None, f"Токен для email {new_user_email} не найден в коллекции confirmtokens"

        invite_code = token_doc.get("tokenHash")
        assert invite_code, "tokenHash отсутствует в документе MongoDB"

    with allure.step("Подтверждение инвайта для нового пользователя"):

        confirm_endpoint = confirm_space_invite_endpoint(
            code=invite_code,
            full_name=full_name,
            password=new_user_password,
            termsAccepted=True
        )

        confirm_resp = owner_client.post(**confirm_endpoint)
        assert confirm_resp.status_code == 200, f"Ошибка подтверждения: {confirm_resp.text}"

        payload = confirm_resp.json().get("payload", {})
        assert payload.get("alreadyAccepted") is False, "Флаг alreadyAccepted должен быть False"
        assert payload.get("spaceId") == space_id_module, "Неверный spaceId в ответе"

    with allure.step("Проверка статуса пользователя в списке участников (должен быть Active)"):
        response = owner_client.post(**get_space_members_endpoint(
            space_id=space_id_module
        ))
        assert response.status_code == 200
        members = response.json().get('payload').get('members')
        target_status = next((s for s in members if s.get('email') == new_user_email), None)

        assert target_status is not None, "Приглашенный пользователь не найден в списке участников"
        assert target_status.get('status') == "Active", "Статус пользователя не изменился на Active"