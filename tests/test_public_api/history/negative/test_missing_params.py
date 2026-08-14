import allure
import pytest

pytestmark = [pytest.mark.public_api]


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative: Missing params")
@pytest.mark.parametrize("missing_param, expected_field_code", [
    ("spaceId", "IncorrectId"),
    ("kind",    "InvalidKind"),
    ("kindId",  "IncorrectId"),
], ids=["missing_spaceId", "missing_kind", "missing_kindId"])
def test_public_history_missing_required_params(public_client, public_space_id, missing_param, expected_field_code):
    """
    При отсутствии любого обязательного параметра (spaceId, kind, kindId) возвращается 400.
    """
    allure.dynamic.title(f"Запрос без обязательного параметра '{missing_param}' возвращает 400 ({expected_field_code})")

    with allure.step(f"Формируем запрос без параметра '{missing_param}'"):
        params = {"spaceId": public_space_id, "kind": "Space", "kindId": public_space_id}
        params.pop(missing_param)

    with allure.step("Отправляем запрос"):
        resp = public_client.get("/public/v1/history", params=params)

    with allure.step(f"Статус ответа 400, error.code = ValidationErrors, {expected_field_code}"):
        assert resp.status_code == 400, \
            f"Ожидался 400 при отсутствии '{missing_param}', получен {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["error"]["code"] == "ValidationErrors", f"Ожидался ValidationErrors: {resp.text}"
        field_codes = body["error"]["fields"][0]["codes"]
        assert expected_field_code in field_codes, \
            f"Ожидался {expected_field_code} в codes: {resp.text}"
