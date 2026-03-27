import allure
import pytest

from config import settings
from test_backend.data.endpoints.Space.space_endpoints import get_spaces_endpoint
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint, confirm_space_invite_endpoint, \
    reactivate_member_endpoint, deactivate_member_endpoint

pytestmark = [pytest.mark.backend]

# Кэш для сохранения member_id между параметризованными запусками теста
_FOREIGN_MEMBER_CACHE = {}


@allure.parent_suite("Invite Service")
@allure.suite("Access Deactivate/Reactivate Space Invitations")
@allure.title("Проверка прав на деактивацию и реактивацию мембера клиентом: {client_fixture}")
@pytest.mark.parametrize(
    "client_fixture, expected_status",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 403),
        ("guest_client", 403),
    ]
)
def test_space_deactivate_reactivate_access_by_role(request, space_with_members, owner_client, foreign_client,
                                                    client_fixture, expected_status):
    """
    Проверка прав доступа к DeactivateMember и ReactivateMember.
    Используется foreign_client: при первом запуске он приглашается и подтверждает инвайт,
    а его member_id кэшируется для последующих параметризованных шагов.
    """
    global _FOREIGN_MEMBER_CACHE
    client = request.getfixturevalue(client_fixture)
    foreign_email = settings.USERS['foreign_client']['email']
    foreign_password = settings.USERS['foreign_client']['password']

    # 1. Получаем member_id из кэша или приглашаем пользователя, если это первый прогон
    member_id = _FOREIGN_MEMBER_CACHE.get(space_with_members)

    if not member_id:
        with allure.step("Owner приглашает foreign_client в пространство (выполняется 1 раз)"):
            invite_resp = owner_client.post(**invite_to_space_endpoint(
                space_id=space_with_members,
                email=foreign_email,
                space_access="Member"
            ))
            assert invite_resp.status_code == 200, f"Ошибка приглашения: {invite_resp.text}"
            member_id = invite_resp.json().get("payload", {}).get("invite", {}).get("_id")

            # Сохраняем для следующих параметров теста
            _FOREIGN_MEMBER_CACHE[space_with_members] = member_id

        with allure.step("foreign_client получает inviteCode и подтверждает инвайт"):
            spaces_resp = foreign_client.post(**get_spaces_endpoint())
            assert spaces_resp.status_code == 200
            spaces = spaces_resp.json().get('payload', {}).get('spaces', [])
            target_space = next((s for s in spaces if s.get('_id') == space_with_members), None)
            assert target_space, "Пространство не найдено в списке спейсов foreign_client"
            invite_code = target_space.get('inviteCode')
            assert invite_code, "inviteCode отсутствует"

            confirm_resp = foreign_client.post(**confirm_space_invite_endpoint(
                code=invite_code,
                full_name="Foreign User",
                password=foreign_password,
                termsAccepted=True
            ))
            assert confirm_resp.status_code == 200, f"Ошибка подтверждения: {confirm_resp.text}"

    # 2. Убедимся, что перед началом теста пользователь реактивирован (для чистоты эксперимента)
    owner_client.post(**reactivate_member_endpoint(space_id=space_with_members, member_id=member_id))

    # 3. Проверка деактивации
    with allure.step(f"Попытка деактивации мембера клиентом {client_fixture}. Ожидаемый статус: {expected_status}"):
        deact_resp = client.post(**deactivate_member_endpoint(
            space_id=space_with_members,
            member_id=member_id
        ))
        assert deact_resp.status_code == expected_status, (
            f"Ошибка доступа при деактивации! Ожидался {expected_status}, получен {deact_resp.status_code}"
        )
        if expected_status == 200:
            with allure.step("Проверка того что пользователю больше не доступен спейс"):
                spaces_resp = foreign_client.post(**get_spaces_endpoint())
                assert spaces_resp.status_code == 200
                spaces = spaces_resp.json().get('payload', {}).get('spaces', [])
                target_space = next((s for s in spaces if s.get('_id') == space_with_members), None)
                assert target_space not in spaces, "Пространство не найдено в списке спейсов"

    # 4. Проверка реактивации
    with allure.step(f"Попытка реактивации мембера клиентом {client_fixture}. Ожидаемый статус: {expected_status}"):
        # Если клиент не смог деактивировать (403), пусть Owner деактивирует его,
        # чтобы мы могли проверить права клиента на реактивацию
        if expected_status != 200:
            owner_client.post(**deactivate_member_endpoint(space_id=space_with_members, member_id=member_id))

        react_resp = client.post(**reactivate_member_endpoint(
            space_id=space_with_members,
            member_id=member_id
        ))
        assert react_resp.status_code == expected_status, (
            f"Ошибка доступа при реактивации! Ожидался {expected_status}, получен {react_resp.status_code}"
        )
        if expected_status == 200:
            with allure.step("Проверка того что пользователю доступен спейс"):
                spaces_resp = foreign_client.post(**get_spaces_endpoint())
                assert spaces_resp.status_code == 200
                spaces = spaces_resp.json().get('payload', {}).get('spaces', [])
                target_space = next((s for s in spaces if s.get('_id') == space_with_members), None)
                assert target_space in spaces, "Пространство не найдено в списке спейсов"