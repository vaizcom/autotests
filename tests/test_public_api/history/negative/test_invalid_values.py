import allure
import pytest

pytestmark = [pytest.mark.public_api]


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative: Invalid values")
@allure.title("Невалидный формат spaceId возвращает 400")
def test_public_history_invalid_space_id_format(public_client, public_space_id):
    """
    spaceId должен быть валидным ObjectId. Невалидный формат возвращает 400.
    """
    with allure.step("Отправляем запрос с невалидным spaceId"):
        resp = public_client.get(
            "/public/v1/history",
            params={"spaceId": "notanobjectid", "kind": "Space", "kindId": public_space_id},
        )

    with allure.step("Статус ответа 400, error.code = ValidationErrors, IncorrectId"):
        assert resp.status_code == 400, \
            f"Ожидался 400, получен {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["error"]["code"] == "ValidationErrors", f"Ожидался ValidationErrors: {resp.text}"
        field_codes = body["error"]["fields"][0]["codes"]
        assert "IncorrectId" in field_codes, f"Ожидался IncorrectId в codes: {resp.text}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative: Invalid values")
@allure.title("Невалидный формат kindId возвращает 400")
def test_public_history_invalid_kind_id_format(public_client, public_space_id):
    """
    kindId должен быть валидным ObjectId. Невалидный формат возвращает 400.
    """
    with allure.step("Отправляем запрос с невалидным kindId"):
        resp = public_client.get(
            "/public/v1/history",
            params={"spaceId": public_space_id, "kind": "Space", "kindId": "notanobjectid"},
        )

    with allure.step("Статус ответа 400, error.code = ValidationErrors, IncorrectId"):
        assert resp.status_code == 400, \
            f"Ожидался 400, получен {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["error"]["code"] == "ValidationErrors", f"Ожидался ValidationErrors: {resp.text}"
        field_codes = body["error"]["fields"][0]["codes"]
        assert "IncorrectId" in field_codes, f"Ожидался IncorrectId в codes: {resp.text}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative: Invalid values")
@pytest.mark.parametrize("invalid_kind, case_id", [
    ("Board", "unsupported_kind_Board"),
    ("space", "lowercase_space"),
    ("SPACE", "uppercase_SPACE"),
    ("123",   "numeric_123"),
], ids=["unsupported_kind_Board", "lowercase_space", "uppercase_SPACE", "numeric_123"])
def test_public_history_invalid_kind(public_client, public_space_id, invalid_kind, case_id):
    """
    kind должен быть одним из допустимых значений enum.
    Любое другое значение возвращает 400.
    """
    allure.dynamic.title(f"Невалидное значение kind='{invalid_kind}' возвращает 400 ({case_id})")
    with allure.step(f"Отправляем запрос с kind='{invalid_kind}'"):
        resp = public_client.get(
            "/public/v1/history",
            params={"spaceId": public_space_id, "kind": invalid_kind, "kindId": public_space_id},
        )

    with allure.step("Статус ответа 400, error.code = ValidationErrors, InvalidKind"):
        assert resp.status_code == 400, \
            f"Ожидался 400 при kind='{invalid_kind}', получен {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["error"]["code"] == "ValidationErrors", f"Ожидался ValidationErrors: {resp.text}"
        field_codes = body["error"]["fields"][0]["codes"]
        assert "InvalidKind" in field_codes, f"Ожидался InvalidKind в codes: {resp.text}"
