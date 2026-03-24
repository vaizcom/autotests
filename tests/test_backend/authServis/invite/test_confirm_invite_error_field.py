import allure
import pytest

from test_backend.data.endpoints.invite.invite_endpoint import (
    confirm_space_invite_endpoint
)

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Confirm Invite Error Field")
@allure.title("Ошибка при пустом коде приглашения")
def test_confirm_space_invite_empty_code(owner_client):
    with allure.step("Попытка подтверждения с пустым кодом (ожидается JwtEmpty)"):
        confirm_resp = owner_client.post(**confirm_space_invite_endpoint(
            code="",
            full_name="Valid Name",
            password="ValidPassword123!",
            termsAccepted=True
        ))

        assert confirm_resp.status_code == 400
        assert confirm_resp.json().get("error", {}).get("code") == "JwtEmpty"


@allure.parent_suite("Auth Service")
@allure.suite("Invite")
@allure.sub_suite("Confirm Invite Error Field")
@pytest.mark.parametrize("full_name, password, terms_accepted, expected_error_code, case_name", [
    (" ", "123456", True, "FieldCantBeBlanc", "empty_full_name"),
    ("full_name", "", True, "PasswordTooShort", "empty_password"),
    ("full_name ", "123456", False, "TermsNotAccepted", "terms_not_accepted"),
],
ids=["empty_full_name", "empty_password", "terms_not_accepted"]
)
def test_confirm_space_invite_invalid_profile(
        owner_client,
        temp_space,
        get_invite_code,
        full_name,
        password,
        terms_accepted,
        expected_error_code,
        case_name
):
    allure.dynamic.title(f"{case_name}. Ошибка подтверждения инвайта при невалидных полях")

    from config import settings
    foreign_email = settings.USERS['owner']['email']

    with allure.step("Подготовка: получение валидного кода инвайта"):
        # Передаем клиента, email и ID пространства
        valid_invite_code = get_invite_code(
            client_to_invite=owner_client,
            email_to_invite=foreign_email,
            space_id=temp_space
        )

    with allure.step(f"Попытка подтверждения с некорректными данными (ожидается {expected_error_code})"):
        confirm_resp = owner_client.post(**confirm_space_invite_endpoint(
            code=valid_invite_code,
            full_name=full_name,
            password=password,
            termsAccepted=terms_accepted
        ))

        assert confirm_resp.status_code == 400
        fields = confirm_resp.json().get("error").get("fields")

        # Собираем все коды ошибок из списка полей (разворачиваем списки в один)
        field_error_codes = []
        for f in fields:
            if isinstance(f, dict) and "codes" in f:
                field_error_codes.extend(f.get("codes"))

        assert expected_error_code in field_error_codes, f"Ожидаемый код '{expected_error_code}' не найден в полях: {fields}"