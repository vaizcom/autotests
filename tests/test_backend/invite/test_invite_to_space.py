import pytest
import allure

from test_backend.data.endpoints.access_group.access_group_helpers import wait_for_member_access_group
from test_backend.data.endpoints.invite.assert_invite_payload import assert_invite_payload
from test_backend.data.endpoints.invite.invite_endpoint import invite_to_space_endpoint

pytestmark = [pytest.mark.backend]


# Параметризация для проверки разных ролей
@allure.parent_suite("Invite Service")
@allure.suite("Space Invitations (set role)")
@pytest.mark.parametrize("role", ["Guest", "Member", "Manager", "Owner"])
@allure.title("Приглашение пользователя в Space с ролью {role}")
def test_invite_to_space(second_main_client, second_space_id, role):
    """
    Тест проверяет приглашение пользователя в спейс с указанной ролью
    и последующую проверку его прав в списке участников.
    """
    # 1. Генерация уникального email для теста
    email = f"invite_{role.lower()}_{second_space_id}@autotest.com"

    # 2. Отправка приглашения
    with allure.step(f"Приглашение пользователя с ролью {role}"):
        response = second_main_client.post(**invite_to_space_endpoint(
            space_id=second_space_id,
            email=email,
            space_access=role
        ))
        assert response.status_code == 200, f"Ошибка приглашения: {response.text}"

        payload = response.json().get("payload", {}).get("invite", {})


        _id = payload.get("_id")

        assert _id, "В ответе инвайта не вернулся _id"

    with allure.step("Валидация тела ответа InviteToSpace"):
        assert_invite_payload(
            invite=payload,
            space_id=second_space_id,
            email=email
        )

    # 3. Прямой запрос прав доступа по полученному ID с универсальным поллингом
    with allure.step("Ожидание появления пользователя в списке групп доступа"):
        target_id = wait_for_member_access_group(second_main_client, second_space_id, _id)

        # Базовые проверки структуры группы
    with allure.step("Базовые проверки структуры созданной группы"):
        assert target_id.get("space") == second_space_id, "ID спейса в группе не совпадает"
        assert isinstance(target_id.get("members"), list), "Поле members должно быть списком"
        assert "createdAt" in target_id, "Отсутствует поле createdAt"
        assert "updatedAt" in target_id, "Отсутствует поле updatedAt"

        # Проверка доступов к проектам и доскам
    with allure.step(f"Проверка доступов к проектам и доскам для роли {role}"):
        if role == "Owner":
            project_accesses = target_id.get("projectAccesses", {})
            board_accesses = target_id.get("boardAccesses", {})
            assert all(val == "Owner" for val in project_accesses.values()), f"Не все права в проектах равны Owner: {project_accesses}"
            assert all(val == "Owner" for val in board_accesses.values()), f"Не все права в досках равны Owner: {board_accesses}"
        else:
            assert target_id.get("projectAccesses") == {}, "Поле projectAccesses должно быть пустым словарем"
            assert target_id.get("boardAccesses") == {}, "Поле boardAccesses должно быть пустым словарем"

        # Проверяем права в spaceAccesses
    with allure.step(f"Проверка соответствия роли {role} в spaceAccesses"):
        space_accesses = target_id.get("spaceAccesses", {})
        actual_role = space_accesses.get(second_space_id)

        assert actual_role == role, (
            f"Роль не совпадает!\n"
            f"Ожидалось: {role}\n"
            f"Получено: {actual_role}\n"
            f"Объект spaceAccesses: {space_accesses}"
        )