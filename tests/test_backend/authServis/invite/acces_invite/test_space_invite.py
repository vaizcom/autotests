import allure
import pytest

from config.generators import generate_email
from core.waiters import wait_until
from test_backend.data.endpoints.access_group.aaccess_group_endpoints import get_access_groups_endpoint
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint, remove_invite_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Access Space Invitations")
@allure.title("Проверка прав на отправку инвайта в Space клиентом: {client_fixture}")
@pytest.mark.parametrize(
    "client_fixture, expected_status",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 403),
        ("guest_client", 403),
    ]
)
def test_space_invite_access_by_role(request, space_with_members, client_fixture, expected_status):
    """
    Проверка, что инвайт в спейс разрешен только пользователям с ролью выше менеджера (Owner, Manager).
    Для ролей Member и Guest ожидается ошибка доступа (обычно 403 Forbidden).
    """
    # 1. Получаем клиента с нужной ролью через request.getfixturevalue
    client = request.getfixturevalue(client_fixture)

    # 2. Генерируем уникальный email-заглушку для попытки инвайта
    email = generate_email()

    # 3. Отправляем запрос от имени этого клиента
    with allure.step(f"Попытка отправки инвайта клиентом {client_fixture}. Ожидаемый статус: {expected_status}"):
        response = client.post(**invite_to_space_endpoint(
            space_id=space_with_members,
            email=email,
            space_access="Member"  # Роль, которую пытаемся выдать, не важна
        ))

        # 4. Проверяем, что сервер ответил ожидаемым статус-кодом
        assert response.status_code == expected_status, (
            f"Права доступа нарушены! Ожидался статус {expected_status} для {client_fixture}, "
            f"но получен {response.status_code}. Ответ сервера: {response.text}"
        )

        # 5. Если инвайт был успешно создан (статус 200), удаляем его
        if expected_status == 200:
            invite_id = response.json().get("payload", {}).get("invite", {}).get("_id")
            if invite_id:
                client.post(**remove_invite_endpoint(space_id=space_with_members, member_id=invite_id))


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Space Invitations - Access Control APP-4623")
@allure.title("Менеджер не может выдать роль Owner при инвайте (роль сбрасывается до Guest , д.б. 400 APP-4623)")
def test_manager_cannot_invite_owner(manager_client, space_with_members):
    """
    Проверка, что менеджер при попытке пригласить пользователя с ролью Owner,
    успешно отправляет инвайт (200 OK), но пользователю фактически назначается роль Guest.
    """
    email = generate_email()

    # 1. Отправляем инвайт с завышенной ролью
    with allure.step("Менеджер отправляет инвайт с ролью Owner"):
        response = manager_client.post(**invite_to_space_endpoint(
            space_id=space_with_members,
            email=email,
            space_access="Owner"
        ))
        assert response.status_code == 200, f"Ошибка приглашения: {response.text}"

        payload = response.json().get("payload", {}).get("invite", {})
        _id = payload.get("_id")
        assert _id, "В ответе инвайта не вернулся _id"

    # 2. Ждем появления группы доступа
    with allure.step("Ожидание появления пользователя в списке групп доступа"):
        def _check_group():
            group_resp = manager_client.post(**get_access_groups_endpoint(space_id=space_with_members))
            assert group_resp.status_code == 200, f"Ошибка GetAccessGroup: {group_resp.text}"
            groups = group_resp.json().get("payload", {}).get("accessGroups", [])
            return next((g for g in groups if g.get("members") == [_id]), None)

        try:
            target_group = wait_until(
                condition_func=_check_group,
                timeout=10,
                error_msg=f"Группа с ID {_id} не появилась в списке accessGroups за 10 секунд."
            )
        except TimeoutError as e:
            pytest.fail(str(e))

    # 3. Проверяем, что роль сбросилась
    with allure.step("Проверка, что роль в spaceAccesses сброшена до Guest"):
        space_accesses = target_group.get("spaceAccesses", {})
        actual_role = space_accesses.get(space_with_members)
        assert actual_role == "Guest", (
            f"Защита от эскалации не сработала!\n"
            f"Ожидалась роль: Guest\n"
            f"Фактическая роль: {actual_role}\n"
            f"Объект spaceAccesses: {space_accesses}"
        )

    # 4. Удаляем инвайт
    with allure.step("Удаление инвайта"):
        remove_resp = manager_client.post(**remove_invite_endpoint(space_id=space_with_members, member_id=_id))
        assert remove_resp.status_code == 200, f"Ошибка при удалении инвайта: {remove_resp.text}"