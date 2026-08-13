import allure
import pytest

_VALID_MONGO_ID = "000000000000000000000001"
FOREIGN_SPACE_ID = "6a2ff49efcc30f1b36f4e0dd"

pytestmark = [pytest.mark.public_api]


# ── 1. Отсутствие обязательных параметров ────────────────────────────────────

@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative")
@allure.title("Запрос без обязательного параметра '{missing_param}' возвращает 400")
@pytest.mark.parametrize("missing_param", ["spaceId", "kind", "kindId"],
                         ids=["missing_spaceId", "missing_kind", "missing_kindId"])
def test_public_history_missing_required_params(public_client, public_space_id, missing_param):
    """
    При отсутствии любого обязательного параметра (spaceId, kind, kindId) возвращается 400.
    """
    with allure.step(f"Формируем запрос без параметра '{missing_param}'"):
        params = {"spaceId": public_space_id, "kind": "Space", "kindId": public_space_id}
        params.pop(missing_param)

    with allure.step("Отправляем запрос"):
        resp = public_client.get("/public/v1/history", params=params)

    with allure.step("Статус ответа 400"):
        assert resp.status_code == 400, \
            f"Ожидался 400 при отсутствии '{missing_param}', получен {resp.status_code}: {resp.text}"


# ── 2. Невалидные значения параметров ────────────────────────────────────────

@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative")
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

    with allure.step("Статус ответа 400"):
        assert resp.status_code == 400, \
            f"Ожидался 400, получен {resp.status_code}: {resp.text}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative")
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

    with allure.step("Статус ответа 400"):
        assert resp.status_code == 400, \
            f"Ожидался 400, получен {resp.status_code}: {resp.text}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative")
@allure.title("Невалидное значение kind='{invalid_kind}' возвращает 400")
@pytest.mark.parametrize("invalid_kind", ["Board", "space", "SPACE", "123"],
                         ids=["random_string", "lowercase", "uppercase", "number"])
def test_public_history_invalid_kind(public_client, public_space_id, invalid_kind):
    """
    kind должен быть одним из допустимых значений enum.
    Любое другое значение возвращает 400.
    """
    with allure.step(f"Отправляем запрос с kind='{invalid_kind}'"):
        resp = public_client.get(
            "/public/v1/history",
            params={"spaceId": public_space_id, "kind": invalid_kind, "kindId": public_space_id},
        )

    with allure.step("Статус ответа 400"):
        assert resp.status_code == 400, \
            f"Ожидался 400 при kind='{invalid_kind}', получен {resp.status_code}: {resp.text}"


# ── 3. Доступ и несуществующие сущности ──────────────────────────────────────
# TODO: ожидаемое поведение уточнить после фикса бага IncorrectId на несуществующих ID

@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative")
@allure.title("Несуществующий spaceId возвращает ValidationErrors/IncorrectId")
def test_public_history_nonexistent_space_id(public_client, public_space_id):
    """
    Запрос с несуществующим spaceId возвращает 200 + ValidationErrors/IncorrectId.
    TODO: уточнить после фикса — ожидается пустой items или другой код ошибки.
    """
    with allure.step("Отправляем запрос с несуществующим spaceId"):
        resp = public_client.get(
            "/public/v1/history",
            params={"spaceId": _VALID_MONGO_ID, "kind": "Space", "kindId": public_space_id},
        )

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, \
            f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Тело содержит ValidationErrors"):
        body = resp.json()
        assert body.get("code") == "ValidationErrors", \
            f"Ожидался code=ValidationErrors, получен: {body.get('code')}, тело: {body}"

    with allure.step("Поле spaceId содержит ошибку IncorrectId"):
        fields = body.get("fields", [])
        space_id_field = next((f for f in fields if f.get("name") == "spaceId"), None)
        assert space_id_field is not None, f"Нет ошибки по полю spaceId: {fields}"
        assert "IncorrectId" in space_id_field.get("codes", []), \
            f"Ожидался код IncorrectId, получен: {space_id_field.get('codes')}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative")
@allure.title("Чужой spaceId возвращает ValidationErrors/IncorrectId")
def test_public_history_foreign_space_id(public_client, public_space_id):
    """
    Запрос к space без доступа возвращает 200 + ValidationErrors/IncorrectId.
    TODO: уточнить после фикса — ожидается пустой items или другой код ошибки.
    """
    with allure.step("Отправляем запрос к чужому space"):
        resp = public_client.get(
            "/public/v1/history",
            params={"spaceId": FOREIGN_SPACE_ID, "kind": "Space", "kindId": public_space_id},
        )

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, \
            f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Тело содержит ValidationErrors"):
        body = resp.json()
        assert body.get("code") == "ValidationErrors", \
            f"Ожидался code=ValidationErrors, получен: {body.get('code')}, тело: {body}"

    with allure.step("Поле spaceId содержит ошибку IncorrectId"):
        fields = body.get("fields", [])
        space_id_field = next((f for f in fields if f.get("name") == "spaceId"), None)
        assert space_id_field is not None, f"Нет ошибки по полю spaceId: {fields}"
        assert "IncorrectId" in space_id_field.get("codes", []), \
            f"Ожидался код IncorrectId, получен: {space_id_field.get('codes')}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative")
@allure.title("Несуществующий kindId для kind='{kind}' — проверка ошибки")
@pytest.mark.parametrize("kind", ["Space", "Project", "Task", "Document", "Milestone"],
                         ids=["Space", "Project", "Task", "Document", "Milestone"])
def test_public_history_nonexistent_kind_id(public_client, public_space_id, kind):
    """
    Запрос с несуществующим kindId для каждого вида сущности.
    На внутреннем API: Space/Project → 403 AccessDenied, Task/Document/Milestone → 400 NotFound.
    TODO: уточнить ожидаемое поведение на публичном API после фикса бага IncorrectId.
    """
    with allure.step(f"Отправляем запрос с kind={kind} и несуществующим kindId"):
        resp = public_client.get(
            "/public/v1/history",
            params={"spaceId": public_space_id, "kind": kind, "kindId": _VALID_MONGO_ID},
        )

    with allure.step(f"Статус ответа {resp.status_code}, тело: {resp.text}"):
        assert resp.status_code in (200, 400, 403, 404), \
            f"Неожиданный статус {resp.status_code}: {resp.text}"
