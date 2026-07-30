import allure
import pytest

pytestmark = [pytest.mark.backend]

_VALID_MONGO_ID = "a" * 24  # валидный формат MongoId, несуществующая сущность


# ──────────────────────────────────────────────────────────────────────────────
# 1. Невалидный kind → 400
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kind отсутствует → 400")
def test_get_history_missing_kind(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory без поля kind"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kind = пустая строка → 400")
def test_get_history_empty_kind(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с kind=''"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "", "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kind = произвольная строка → 400 с кодом InvalidKind")
def test_get_history_invalid_string_kind(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с kind='WRONG'"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "WRONG", "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400, в error.fields — код InvalidKind"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"
        field_codes = [c for f in resp.json()["error"]["fields"] for c in f.get("codes", [])]
        assert "InvalidKind" in field_codes


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kind = число → 400")
def test_get_history_numeric_kind(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с kind=0"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": 0, "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kind = null → 400")
def test_get_history_null_kind(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с kind=null"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": None, "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kind='Board' — в EKind, но не в HISTORY_KINDS → 400")
def test_get_history_kind_board_rejected(main_client, main_space):
    """Board исключён из HISTORY_KINDS — validators must reject."""
    with allure.step("Отправляем POST /GetHistory с kind='Board'"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Board", "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400"):
        assert resp.status_code == 400


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kind='Member' — в EKind, но не в HISTORY_KINDS → 400")
def test_get_history_kind_member_rejected(main_client, main_space):
    """Member исключён из HISTORY_KINDS — validators must reject."""
    with allure.step("Отправляем POST /GetHistory с kind='Member'"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Member", "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400"):
        assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
# 2. Невалидный kindId → 400
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kindId отсутствует → 400")
def test_get_history_missing_kind_id(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory без поля kindId"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Task"},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kindId = пустая строка → 400")
def test_get_history_empty_kind_id(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с kindId=''"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Task", "kindId": ""},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kindId = 'abc' (не MongoId) → 400")
def test_get_history_short_kind_id(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с kindId='abc'"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Task", "kindId": "abc"},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400, в error.fields — ошибка mongodb id"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"
        field_codes = [c for f in resp.json()["error"]["fields"] for c in f.get("codes", [])]
        assert any("mongodb id" in c for c in field_codes)


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kindId = 25 символов (длиннее MongoId) → 400")
def test_get_history_long_kind_id(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с kindId длиной 25 символов"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Task", "kindId": "a" * 25},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kindId = число → 400")
def test_get_history_numeric_kind_id(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с kindId=123"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Task", "kindId": 123},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: kindId = null → 400")
def test_get_history_null_kind_id(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с kindId=null"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": "Task", "kindId": None},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Оба обязательных поля отсутствуют
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.title("GetHistory: пустое тело {} → 400, ошибки по обоим полям")
def test_get_history_empty_body(main_client, main_space):
    with allure.step("Отправляем POST /GetHistory с пустым телом {}"):
        resp = main_client.post(
            path="/GetHistory",
            json={},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400, не менее 2 ошибок в error.fields"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"
        assert len(resp.json()["error"]["fields"]) >= 2
