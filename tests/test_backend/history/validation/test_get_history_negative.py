import allure
import pytest

from core.response_utils import short_resp

pytestmark = [pytest.mark.backend]

_VALID_MONGO_ID = "a" * 24  # валидный формат MongoId, несуществующая сущность
_MISSING = object()  # sentinel — поле не передаётся в запросе

# Доступные kind для GetHistory: Space, Project, Task, Document, Milestone
# Запрещённые (есть в EKind, но нет в HISTORY_KINDS): Board, Member


# ──────────────────────────────────────────────────────────────────────────────
# 1. Невалидный kind → 400
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.sub_suite("Negative: невалидный kind")
@pytest.mark.parametrize("kind_value, case", [
    (_MISSING, "kind отсутствует"),
    ("",       "kind = пустая строка"),
    ("WRONG",  "kind = произвольная строка"),
], ids=["missing", "empty", "wrong_string"])
def test_get_history_invalid_kind(main_client, main_space, kind_value, case):
    """Невалидное значение kind должно вернуть 400 (InvalidForm)."""
    allure.dynamic.title(f"GetHistory: {case} → 400 (InvalidForm)")

    body = {"kindId": _VALID_MONGO_ID}
    if kind_value is not _MISSING:
        body["kind"] = kind_value

    with allure.step(f"Отправляем POST /GetHistory: {case}"):
        resp = main_client.post(
            path="/GetHistory", json=body,
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 (InvalidForm)"):
        assert resp.status_code == 400, f"Ожидали 400 (InvalidForm), получили: {short_resp(resp)}"
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.sub_suite("Negative: невалидный kind")
@pytest.mark.parametrize("kind", ["Board", "Member"], ids=["board", "member"])
def test_get_history_rejected_kind(main_client, main_space, kind):
    """kind есть в EKind, но исключён из HISTORY_KINDS — историю для них через GetHistory запросить нельзя,
    должен вернуть 400 (Bad Request)."""
    allure.dynamic.title(f"GetHistory: kind='{kind}' — не в HISTORY_KINDS → 400 (Bad Request)")

    with allure.step(f"Отправляем POST /GetHistory с kind='{kind}'"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 (Bad Request)"):
        assert resp.status_code == 400, f"Ожидали 400 (Bad Request), получили: {short_resp(resp)}"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Невалидный kindId → 400
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.sub_suite("Negative: невалидный kindId")
@pytest.mark.parametrize("kind_id_value, case", [
    (_MISSING, "kindId отсутствует"),
    ("abc",    "kindId = 'abc' (не MongoId)"),
], ids=["missing", "invalid_format"])
def test_get_history_invalid_kind_id(main_client, main_space, kind_id_value, case):
    """Невалидное значение kindId должно вернуть 400 (InvalidForm)."""
    allure.dynamic.title(f"GetHistory: {case} → 400 (InvalidForm)")

    body = {"kind": "Task"}
    if kind_id_value is not _MISSING:
        body["kindId"] = kind_id_value

    with allure.step(f"Отправляем POST /GetHistory: {case}"):
        resp = main_client.post(
            path="/GetHistory", json=body,
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 (InvalidForm)"):
        assert resp.status_code == 400, f"Ожидали 400 (InvalidForm), получили: {short_resp(resp)}"
        assert resp.json()["error"]["code"] == "InvalidForm"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Несуществующая сущность → 403 или 400
#    Space/Project → 403 (Forbidden), Task/Document/Milestone → 400
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.sub_suite("Negative: несуществующая сущность")
@pytest.mark.parametrize("kind,expected_status,expected_error_code", [
    ("Space",     403, "AccessDenied"),
    ("Project",   403, "AccessDenied"),
    ("Task",      400, "NotFound"),
    ("Document",  400, "NotFound"),
    ("Milestone", 400, "NotFound"),
], ids=["space", "project", "task", "document", "milestone"])
def test_get_history_nonexistent_entity(main_client, main_space, kind, expected_status, expected_error_code):
    """Валидный kind + валидный формат kindId, но несуществующая сущность."""
    allure.dynamic.title(f"GetHistory: kind='{kind}', kindId несуществующий → {expected_status} ({expected_error_code})")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}', kindId='{_VALID_MONGO_ID}'"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step(f"Получаем {expected_status} ({expected_error_code}) — сущность не существует"):
        assert resp.status_code == expected_status, f"Ожидали {expected_status} ({expected_error_code}), получили: {short_resp(resp)}"
        assert resp.json()["error"]["code"] == expected_error_code, f"Ожидали error.code='{expected_error_code}', получили: {short_resp(resp)}"
