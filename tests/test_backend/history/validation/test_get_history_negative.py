import allure
import pytest

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
@allure.sub_suite("Negative")
@pytest.mark.parametrize("kind_value, case", [
    (_MISSING, "kind отсутствует"),
    ("",       "kind = пустая строка"),
    ("WRONG",  "kind = произвольная строка"),
], ids=["missing", "empty", "wrong_string"])
def test_get_history_invalid_kind(main_client, main_space, kind_value, case):
    """Невалидное значение kind должно вернуть 400 InvalidForm."""
    allure.dynamic.title(f"GetHistory: {case} → 400")

    body = {"kindId": _VALID_MONGO_ID}
    if kind_value is not _MISSING:
        body["kind"] = kind_value

    with allure.step(f"Отправляем POST /GetHistory: {case}"):
        resp = main_client.post(
            path="/GetHistory", json=body,
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.sub_suite("Negative")
@pytest.mark.parametrize("kind", ["Board", "Member"], ids=["board", "member"])
def test_get_history_rejected_kind(main_client, main_space, kind):
    """kind есть в EKind, но исключён из HISTORY_KINDS — историю для них через GetHistory запросить нельзя,
    должен вернуть 400."""
    allure.dynamic.title(f"GetHistory: kind='{kind}' — не в HISTORY_KINDS → 400")

    with allure.step(f"Отправляем POST /GetHistory с kind='{kind}'"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400"):
        assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
# 2. Невалидный kindId → 400
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.sub_suite("Negative")
@pytest.mark.parametrize("kind_id_value, case", [
    (_MISSING, "kindId отсутствует"),
    ("abc",    "kindId = 'abc' (не MongoId)"),
], ids=["missing", "invalid_format"])
def test_get_history_invalid_kind_id(main_client, main_space, kind_id_value, case):
    """Невалидное значение kindId должно вернуть 400 InvalidForm."""
    allure.dynamic.title(f"GetHistory: {case} → 400")

    body = {"kind": "Task"}
    if kind_id_value is not _MISSING:
        body["kindId"] = kind_id_value

    with allure.step(f"Отправляем POST /GetHistory: {case}"):
        resp = main_client.post(
            path="/GetHistory", json=body,
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )
    with allure.step("Получаем 400 InvalidForm"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Несуществующая сущность → 403
# ──────────────────────────────────────────────────────────────────────────────

@allure.parent_suite("History Service")
@allure.suite("GetHistory Validation")
@allure.sub_suite("Negative")
@pytest.mark.parametrize("kind", [
    "Space", "Project", "Task", "Document", "Milestone",
], ids=["space", "project", "task", "document", "milestone"])
def test_get_history_nonexistent_entity(main_client, main_space, kind):
    """Валидный kind + валидный формат kindId, но несуществующая сущность → 403."""
    allure.dynamic.title(f"GetHistory: kind='{kind}', kindId несуществующий → 403")

    with allure.step(f"Отправляем POST /GetHistory: kind='{kind}', kindId='{_VALID_MONGO_ID}'"):
        resp = main_client.post(
            path="/GetHistory",
            json={"kind": kind, "kindId": _VALID_MONGO_ID},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 403 — сущность не существует, доступ запрещён"):
        assert resp.status_code == 403
