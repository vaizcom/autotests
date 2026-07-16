import allure
import pytest
from config.generators import generate_custom_field_title
from test_backend.data.endpoints.Board.board_endpoints import (
    create_board_custom_field_endpoint,
    edit_board_custom_field_endpoint,
)

pytestmark = [pytest.mark.backend]

RESERVED_NAMES = [
    pytest.param("sort", id="sort"),
    pytest.param("group", id="group"),
    pytest.param("empty", id="empty"),
    pytest.param("not_empty", id="not_empty"),
    pytest.param("true", id="true"),
    pytest.param("false", id="false"),
    pytest.param("null", id="null"),
    pytest.param("priority", id="priority"),
    pytest.param("columns", id="columns", marks=pytest.mark.xfail(reason="Сервер пока не блокирует", strict=False)),
    pytest.param("scope", id="scope", marks=pytest.mark.xfail(reason="Сервер пока не блокирует", strict=False)),
    pytest.param("pin", id="pin", marks=pytest.mark.xfail(reason="Сервер пока не блокирует", strict=False)),
    pytest.param("Date", id="Date", marks=pytest.mark.xfail(reason="Сервер пока не блокирует", strict=False)),
]


@allure.parent_suite("Board Service")
@allure.suite("Custom Field Reserved Names")
@pytest.mark.parametrize("reserved_name", RESERVED_NAMES)
@allure.title("Создание кастомного поля с зарезервированным именем: {reserved_name}")
def test_create_custom_field_reserved_name(main_client, temp_board, temp_space, reserved_name):
    """Нельзя создать custom field с зарезервированным именем."""
    with allure.step(f"Создание поля с именем '{reserved_name}'"):
        response = main_client.post(
            **create_board_custom_field_endpoint(
                board_id=temp_board, space_id=temp_space, name=reserved_name, type="Text"
            )
        )

    with allure.step("Проверка ошибки CustomFieldNameReserved"):
        assert response.status_code == 400, f"Ожидали 400, получили {response.status_code}: {response.text}"
        error = response.json().get("error", {})
        fields = error.get("fields", [])
        codes = [f["codes"] for f in fields if f.get("name") == "name"]
        assert any("CustomFieldNameReserved" in c for c in codes), (
            f"Ожидали CustomFieldNameReserved, получили: {error}"
        )


@allure.parent_suite("Board Service")
@allure.suite("Custom Field Reserved Names")
@pytest.mark.parametrize("reserved_name", RESERVED_NAMES)
@allure.title("Создание кастомного поля с зарезервированным именем (case-insensitive): {reserved_name}")
def test_create_custom_field_reserved_name_case_insensitive(main_client, temp_board, temp_space, reserved_name):
    """Проверка case-insensitive: 'Sort', 'SORT', 'sOrT' — все должны блокироваться."""
    upper_name = reserved_name.upper() if reserved_name[0].islower() else reserved_name.lower()

    with allure.step(f"Создание поля с именем '{upper_name}' (другой регистр от '{reserved_name}')"):
        response = main_client.post(
            **create_board_custom_field_endpoint(
                board_id=temp_board, space_id=temp_space, name=upper_name, type="Text"
            )
        )

    with allure.step("Проверка ошибки CustomFieldNameReserved"):
        assert response.status_code == 400, f"Ожидали 400, получили {response.status_code}: {response.text}"
        error = response.json().get("error", {})
        fields = error.get("fields", [])
        codes = [f["codes"] for f in fields if f.get("name") == "name"]
        assert any("CustomFieldNameReserved" in c for c in codes), (
            f"Ожидали CustomFieldNameReserved, получили: {error}"
        )


@allure.parent_suite("Board Service")
@allure.suite("Custom Field Reserved Names")
@allure.title("Нельзя переименовать custom field в зарезервированное имя")
def test_rename_custom_field_to_reserved_name(main_client, temp_board, temp_space):
    """Переименование существующего поля в зарезервированное имя должно вернуть ошибку."""
    title = generate_custom_field_title()

    with allure.step(f"Создание поля с валидным именем '{title}'"):
        create_resp = main_client.post(
            **create_board_custom_field_endpoint(
                board_id=temp_board, space_id=temp_space, name=title, type="Text"
            )
        )
        assert create_resp.status_code == 200, f"Создание не удалось: {create_resp.text}"
        field_id = create_resp.json()["payload"]["customField"]["_id"]

    with allure.step("Переименование поля в 'sort'"):
        edit_resp = main_client.post(
            **edit_board_custom_field_endpoint(
                board_id=temp_board, space_id=temp_space, field_id=field_id, name="sort"
            )
        )

    with allure.step("Проверка ошибки CustomFieldNameReserved"):
        assert edit_resp.status_code == 400, f"Ожидали 400, получили {edit_resp.status_code}: {edit_resp.text}"
        error = edit_resp.json().get("error", {})
        fields = error.get("fields", [])
        codes = [f["codes"] for f in fields if f.get("name") == "name"]
        assert any("CustomFieldNameReserved" in c for c in codes), (
            f"Ожидали CustomFieldNameReserved, получили: {error}"
        )


@allure.parent_suite("Board Service")
@allure.suite("Custom Field Reserved Names")
@allure.title("Нельзя создать custom field с дублирующимся именем на борде")
def test_create_custom_field_duplicate_name(main_client, temp_board, temp_space):
    """Создание двух полей с одинаковым именем на одной борде должно вернуть ошибку."""
    title = generate_custom_field_title()

    with allure.step(f"Создание первого поля с именем '{title}'"):
        resp1 = main_client.post(
            **create_board_custom_field_endpoint(
                board_id=temp_board, space_id=temp_space, name=title, type="Text"
            )
        )
        assert resp1.status_code == 200, f"Создание первого поля не удалось: {resp1.text}"

    with allure.step(f"Создание второго поля с тем же именем '{title}'"):
        resp2 = main_client.post(
            **create_board_custom_field_endpoint(
                board_id=temp_board, space_id=temp_space, name=title, type="Number"
            )
        )

    with allure.step("Проверка ошибки CustomFieldNameReserved"):
        assert resp2.status_code == 400, f"Ожидали 400, получили {resp2.status_code}: {resp2.text}"
        error = resp2.json().get("error", {})
        fields = error.get("fields", [])
        codes = [f["codes"] for f in fields if f.get("name") == "name"]
        assert any("CustomFieldNameReserved" in c for c in codes), (
            f"Ожидали CustomFieldNameReserved, получили: {error}"
        )
