import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import (
    create_board_custom_field_endpoint,
    get_board_endpoint,
    reorder_board_custom_field_endpoint,
)

pytestmark = [pytest.mark.backend]

FAKE_ID = "000000000000000000000000"
MIN_FIELDS = 3
FIELD_NAMES = ["_reorder_cf_1", "_reorder_cf_2", "_reorder_cf_3"]


def _get_fields_order(client, board_id, space_id):
    """Возвращает список _id custom fields в текущем порядке."""
    resp = client.post(**get_board_endpoint(board_id, space_id))
    assert resp.status_code == 200, resp.text
    return [f["_id"] for f in resp.json()["payload"]["board"]["customFields"]]


def _reorder_and_check(client, board_id, space_id, field_id, from_index, to_index, expected_index):
    """Перемещает поле, проверяет позицию, восстанавливает и проверяет восстановление."""
    original = _get_fields_order(client, board_id, space_id)

    with allure.step(f"Перемещаем поле fromIndex={from_index} → toIndex={to_index}"):
        resp = client.post(**reorder_board_custom_field_endpoint(
            board_id=board_id, space_id=space_id,
            field_id=field_id, from_index=from_index, to_index=to_index,
        ))

    with allure.step("Проверяем ответ"):
        assert resp.status_code == 200, f"Ожидали 200, получили: {resp.status_code}"
        new_fields = [f["_id"] for f in resp.json()["payload"]["customFields"]]
        assert new_fields[expected_index] == field_id, (
            f"Поле не на позиции [{expected_index}]: {new_fields}"
        )

    with allure.step("Восстанавливаем порядок"):
        actual_pos = new_fields.index(field_id)
        client.post(**reorder_board_custom_field_endpoint(
            board_id=board_id, space_id=space_id,
            field_id=field_id, from_index=actual_pos, to_index=from_index,
        ))
        restored = _get_fields_order(client, board_id, space_id)
        assert restored == original, f"Порядок не восстановлен: {restored}"


@pytest.fixture(scope="module", autouse=True)
def _ensure_custom_fields(owner_client, main_space, main_board):
    """Гарантирует, что на main_board есть минимум 3 custom fields для тестов."""
    resp = owner_client.post(**get_board_endpoint(main_board, main_space))
    assert resp.status_code == 200, resp.text
    existing = resp.json()["payload"]["board"]["customFields"]
    existing_names = {f["name"] for f in existing}

    if len(existing) >= MIN_FIELDS:
        return

    for name in FIELD_NAMES:
        if name not in existing_names:
            r = owner_client.post(**create_board_custom_field_endpoint(
                board_id=main_board, space_id=main_space, name=name, type="Text",
            ))
            assert r.status_code == 200, f"Ошибка создания поля {name}: {r.text}"

    final = _get_fields_order(owner_client, main_board, main_space)
    assert len(final) >= MIN_FIELDS, (
        f"Не удалось обеспечить {MIN_FIELDS} полей, найдено: {len(final)}"
    )


# ─── Positive ────────────────────────────────────────────────────────────────


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Custom Field")
@allure.sub_suite("Positive")
@allure.title("Успешная перестановка поля с позиции 1 на позицию 0")
def test_reorder_field_success(owner_client, main_space, main_board):
    """Перемещаем второе поле на первую позицию, проверяем что порядок изменился."""
    original = _get_fields_order(owner_client, main_board, main_space)
    assert len(original) >= 2, f"Нужно минимум 2 поля, найдено: {len(original)}"
    _reorder_and_check(
        owner_client, main_board, main_space,
        field_id=original[1], from_index=1, to_index=0, expected_index=0,
    )


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Custom Field")
@allure.sub_suite("Positive")
@allure.title("Перемещение поля в конец списка")
def test_reorder_field_to_end(owner_client, main_space, main_board):
    """Перемещаем первое поле на последнюю позицию."""
    original = _get_fields_order(owner_client, main_board, main_space)
    _reorder_and_check(
        owner_client, main_board, main_space,
        field_id=original[0], from_index=0, to_index=len(original) - 1, expected_index=-1,
    )


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Custom Field")
@allure.sub_suite("Positive")
@allure.title("Перемещение поля на ту же позицию — порядок не меняется")
def test_reorder_field_same_index(owner_client, main_space, main_board):
    """Одинаковые индексы → 200, порядок не изменился."""
    original = _get_fields_order(owner_client, main_board, main_space)

    with allure.step("Перемещаем поле на ту же позицию"):
        resp = owner_client.post(**reorder_board_custom_field_endpoint(
            board_id=main_board, space_id=main_space,
            field_id=original[1], from_index=1, to_index=1,
        ))

    with allure.step("Проверяем, что порядок не изменился"):
        assert resp.status_code == 200, resp.text
        new_fields = [f["_id"] for f in resp.json()["payload"]["customFields"]]
        assert new_fields == original, f"Порядок изменился: {new_fields}"


# ─── Negative: IncorrectMoveFromIndex ────────────────────────────────────────


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Custom Field")
@allure.sub_suite("Negative")
@allure.title("Неверный fromIndex (поле на позиции 0, передаём 2) → IncorrectMoveFromIndex")
def test_reorder_field_wrong_from_index(owner_client, main_space, main_board):
    """fieldId на позиции 0, передаём fromIndex=2 → 400."""
    original = _get_fields_order(owner_client, main_board, main_space)

    with allure.step("Передаём неверный fromIndex"):
        resp = owner_client.post(**reorder_board_custom_field_endpoint(
            board_id=main_board, space_id=main_space,
            field_id=original[0], from_index=2, to_index=1,
        ))

    with allure.step("Проверяем ошибку IncorrectMoveFromIndex"):
        assert resp.status_code == 400, f"Ожидали 400, получили: {resp.status_code}"
        assert resp.json()["error"]["code"] == "IncorrectMoveFromIndex"

    with allure.step("Проверяем, что порядок не изменился"):
        current = _get_fields_order(owner_client, main_board, main_space)
        assert current == original


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Custom Field")
@allure.sub_suite("Negative")
@allure.title("Несуществующий fieldId → IncorrectMoveFromIndex")
def test_reorder_field_invalid_field_id(owner_client, main_space, main_board):
    """Несуществующий fieldId → 400 IncorrectMoveFromIndex."""
    with allure.step("Передаём несуществующий fieldId"):
        resp = owner_client.post(**reorder_board_custom_field_endpoint(
            board_id=main_board, space_id=main_space,
            field_id=FAKE_ID, from_index=0, to_index=1,
        ))

    with allure.step("Проверяем ошибку IncorrectMoveFromIndex"):
        assert resp.status_code == 400, f"Ожидали 400, получили: {resp.status_code}"
        assert resp.json()["error"]["code"] == "IncorrectMoveFromIndex"


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Custom Field")
@allure.sub_suite("Negative")
@allure.title("Отрицательный fromIndex=-1 → IncorrectMoveFromIndex")
def test_reorder_field_negative_from_index(owner_client, main_space, main_board):
    """fromIndex=-1 → 400 IncorrectMoveFromIndex."""
    original = _get_fields_order(owner_client, main_board, main_space)

    with allure.step("Передаём fromIndex=-1"):
        resp = owner_client.post(**reorder_board_custom_field_endpoint(
            board_id=main_board, space_id=main_space,
            field_id=original[0], from_index=-1, to_index=0,
        ))

    with allure.step("Проверяем ошибку IncorrectMoveFromIndex"):
        assert resp.status_code == 400, f"Ожидали 400, получили: {resp.status_code}"
        assert resp.json()["error"]["code"] == "IncorrectMoveFromIndex"


# ─── Negative: AccessDenied ──────────────────────────────────────────────────


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Custom Field")
@allure.sub_suite("Negative")
@allure.title("Несуществующий boardId → AccessDenied")
def test_reorder_field_invalid_board_id(owner_client, main_space, main_board):
    """Несуществующий boardId → 403 AccessDenied."""
    original = _get_fields_order(owner_client, main_board, main_space)

    with allure.step("Передаём несуществующий boardId"):
        resp = owner_client.post(**reorder_board_custom_field_endpoint(
            board_id=FAKE_ID, space_id=main_space,
            field_id=original[0], from_index=0, to_index=1,
        ))

    with allure.step("Проверяем ошибку AccessDenied"):
        assert resp.status_code == 403, f"Ожидали 403, получили: {resp.status_code}"
        assert resp.json()["error"]["code"] == "AccessDenied"


# ─── Negative: arrayMove — перемещение в конец ───────────────────────────────


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Custom Field")
@allure.sub_suite("Negative")
@pytest.mark.parametrize(
    "to_index",
    [
        pytest.param(-1, id="toIndex=-1"),
        pytest.param(999, id="toIndex=999"),
    ],
)
@allure.title("toIndex={to_index} — элемент перемещается в конец (arrayMove)")
def test_reorder_field_moves_to_end(owner_client, main_space, main_board, to_index):
    """
    arrayMove интерпретирует toIndex за пределами массива как последний элемент.
    Фиксируем текущее поведение API.
    """
    original = _get_fields_order(owner_client, main_board, main_space)
    _reorder_and_check(
        owner_client, main_board, main_space,
        field_id=original[0], from_index=0, to_index=to_index, expected_index=-1,
    )
