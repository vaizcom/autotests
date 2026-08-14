import allure
import pytest

_VALID_MONGO_ID = "000000000000000000000001"
FOREIGN_SPACE_ID = "6a2ff49efcc30f1b36f4e0dd"

pytestmark = [pytest.mark.public_api]


# TODO: ожидаемое поведение уточнить после фикса бага IncorrectId на несуществующих ID

@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative: несуществующий spaceId")
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
@allure.sub_suite("Negative: чужой spaceId")
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


# BUG: все kind возвращают 500 при несуществующем kindId
# Ожидаемое поведение: Space/Project → 403, Task/Document/Milestone → 400
@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative: несуществующий kindId")
@allure.title("Несуществующий kindId для kind='{kind}' возвращает 500 (BUG)")
@pytest.mark.xfail(reason="BUG: сервер возвращает 500 вместо корректного кода ошибки", strict=True)
@pytest.mark.parametrize("kind", ["Space", "Project", "Task", "Document", "Milestone"],
                         ids=["Space", "Project", "Task", "Document", "Milestone"])
def test_public_history_nonexistent_kind_id(public_client, public_space_id, kind):
    """
    Запрос с несуществующим kindId для каждого вида сущности.
    BUG: все kind возвращают 500 — сервер не обрабатывает случай несуществующей сущности.
    Ожидаемое поведение после фикса: Space/Project → 403 AccessDenied, Task/Document/Milestone → 400 NotFound.
    """
    with allure.step(f"Отправляем запрос с kind={kind} и несуществующим kindId"):
        resp = public_client.get(
            "/public/v1/history",
            params={"spaceId": public_space_id, "kind": kind, "kindId": _VALID_MONGO_ID},
        )

    with allure.step("Статус ответа не должен быть 500"):
        assert resp.status_code != 500, \
            f"BUG: сервер вернул 500 при kind={kind}, kindId={_VALID_MONGO_ID}: {resp.text}"
