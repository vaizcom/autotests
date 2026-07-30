import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import (
    get_board_endpoint,
    reorder_board_type_endpoint,
)

pytestmark = [pytest.mark.backend]

FAKE_ID = "000000000000000000000000"


def _get_types_order(client, board_id, space_id):
    """Возвращает список _id типов в текущем порядке."""
    resp = client.post(**get_board_endpoint(board_id, space_id))
    assert resp.status_code == 200, resp.text
    return [t["_id"] for t in resp.json()["payload"]["board"]["typesList"]]


def _reorder_and_check(client, board_id, space_id, type_id, from_index, to_index, expected_index):
    """Перемещает тип, проверяет позицию, восстанавливает и проверяет восстановление."""
    original = _get_types_order(client, board_id, space_id)

    with allure.step(f"Перемещаем тип fromIndex={from_index} → toIndex={to_index}"):
        resp = client.post(**reorder_board_type_endpoint(
            board_id=board_id, space_id=space_id,
            board_type_id=type_id, from_index=from_index, to_index=to_index,
        ))

    with allure.step("Проверяем ответ"):
        assert resp.status_code == 200, f"Ожидали 200, получили: {resp.status_code}"
        new_types = [t["_id"] for t in resp.json()["payload"]["typesList"]]
        assert new_types[expected_index] == type_id, (
            f"Тип не на позиции [{expected_index}]: {new_types}"
        )

    with allure.step("Восстанавливаем порядок"):
        actual_pos = new_types.index(type_id)
        client.post(**reorder_board_type_endpoint(
            board_id=board_id, space_id=space_id,
            board_type_id=type_id, from_index=actual_pos, to_index=from_index,
        ))
        restored = _get_types_order(client, board_id, space_id)
        assert restored == original, f"Порядок не восстановлен: {restored}"


# ─── Positive ────────────────────────────────────────────────────────────────


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Type")
@allure.sub_suite("Positive")
@allure.title("Успешная перестановка типа с позиции 1 на позицию 0")
def test_reorder_type_success(owner_client, main_space, main_board):
    """Перемещаем второй тип на первую позицию, проверяем что порядок изменился."""
    original = _get_types_order(owner_client, main_board, main_space)
    assert len(original) >= 2, f"Нужно минимум 2 типа, найдено: {len(original)}"
    _reorder_and_check(
        owner_client, main_board, main_space,
        type_id=original[1], from_index=1, to_index=0, expected_index=0,
    )


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Type")
@allure.sub_suite("Positive")
@allure.title("Перемещение типа в конец списка")
def test_reorder_type_to_end(owner_client, main_space, main_board):
    """Перемещаем первый тип на последнюю позицию."""
    original = _get_types_order(owner_client, main_board, main_space)
    _reorder_and_check(
        owner_client, main_board, main_space,
        type_id=original[0], from_index=0, to_index=len(original) - 1, expected_index=-1,
    )


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Type")
@allure.sub_suite("Positive")
@allure.title("Перемещение типа на ту же позицию — порядок не меняется")
def test_reorder_type_same_index(owner_client, main_space, main_board):
    """Одинаковые индексы → 200, порядок не изменился."""
    original = _get_types_order(owner_client, main_board, main_space)

    with allure.step("Перемещаем тип на ту же позицию"):
        resp = owner_client.post(**reorder_board_type_endpoint(
            board_id=main_board, space_id=main_space,
            board_type_id=original[0], from_index=0, to_index=0,
        ))

    with allure.step("Проверяем, что порядок не изменился"):
        assert resp.status_code == 200, resp.text
        new_types = [t["_id"] for t in resp.json()["payload"]["typesList"]]
        assert new_types == original, f"Порядок изменился: {new_types}"


# ─── Negative: IncorrectMoveFromIndex ────────────────────────────────────────


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Type")
@allure.sub_suite("Negative")
@allure.title("Неверный fromIndex (тип на позиции 0, передаём 2) → IncorrectMoveFromIndex")
def test_reorder_type_wrong_from_index(owner_client, main_space, main_board):
    """typeId на позиции 0, передаём fromIndex=2 → 400."""
    original = _get_types_order(owner_client, main_board, main_space)

    with allure.step("Передаём неверный fromIndex"):
        resp = owner_client.post(**reorder_board_type_endpoint(
            board_id=main_board, space_id=main_space,
            board_type_id=original[0], from_index=2, to_index=1,
        ))

    with allure.step("Проверяем ошибку IncorrectMoveFromIndex"):
        assert resp.status_code == 400, f"Ожидали 400, получили: {resp.status_code}"
        assert resp.json()["error"]["code"] == "IncorrectMoveFromIndex"

    with allure.step("Проверяем, что порядок не изменился"):
        current = _get_types_order(owner_client, main_board, main_space)
        assert current == original


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Type")
@allure.sub_suite("Negative")
@allure.title("Несуществующий boardTypeId → IncorrectMoveFromIndex")
def test_reorder_type_invalid_type_id(owner_client, main_space, main_board):
    """Несуществующий boardTypeId → 400 IncorrectMoveFromIndex."""
    with allure.step("Передаём несуществующий boardTypeId"):
        resp = owner_client.post(**reorder_board_type_endpoint(
            board_id=main_board, space_id=main_space,
            board_type_id=FAKE_ID, from_index=0, to_index=1,
        ))

    with allure.step("Проверяем ошибку IncorrectMoveFromIndex"):
        assert resp.status_code == 400, f"Ожидали 400, получили: {resp.status_code}"
        assert resp.json()["error"]["code"] == "IncorrectMoveFromIndex"


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Type")
@allure.sub_suite("Negative")
@allure.title("Отрицательный fromIndex=-1 → IncorrectMoveFromIndex")
def test_reorder_type_negative_from_index(owner_client, main_space, main_board):
    """fromIndex=-1 → 400 IncorrectMoveFromIndex."""
    original = _get_types_order(owner_client, main_board, main_space)

    with allure.step("Передаём fromIndex=-1"):
        resp = owner_client.post(**reorder_board_type_endpoint(
            board_id=main_board, space_id=main_space,
            board_type_id=original[0], from_index=-1, to_index=0,
        ))

    with allure.step("Проверяем ошибку IncorrectMoveFromIndex"):
        assert resp.status_code == 400, f"Ожидали 400, получили: {resp.status_code}"
        assert resp.json()["error"]["code"] == "IncorrectMoveFromIndex"


# ─── Negative: AccessDenied ──────────────────────────────────────────────────


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Type")
@allure.sub_suite("Negative")
@allure.title("Несуществующий boardId → AccessDenied")
def test_reorder_type_invalid_board_id(owner_client, main_space, main_board):
    """Несуществующий boardId → 403 AccessDenied."""
    original = _get_types_order(owner_client, main_board, main_space)

    with allure.step("Передаём несуществующий boardId"):
        resp = owner_client.post(**reorder_board_type_endpoint(
            board_id=FAKE_ID, space_id=main_space,
            board_type_id=original[0], from_index=0, to_index=1,
        ))

    with allure.step("Проверяем ошибку AccessDenied"):
        assert resp.status_code == 403, f"Ожидали 403, получили: {resp.status_code}"
        assert resp.json()["error"]["code"] == "AccessDenied"


# ─── Negative: arrayMove — перемещение в конец ───────────────────────────────


@allure.parent_suite("Board Service")
@allure.suite("Reorder Board Type")
@allure.sub_suite("Negative")
@pytest.mark.parametrize(
    "to_index",
    [
        pytest.param(-1, id="toIndex=-1"),
        pytest.param(999, id="toIndex=999"),
    ],
)
@allure.title("toIndex={to_index} — элемент перемещается в конец (arrayMove)")
def test_reorder_type_moves_to_end(owner_client, main_space, main_board, to_index):
    """
    arrayMove интерпретирует toIndex за пределами массива как последний элемент.
    Фиксируем текущее поведение API.
    """
    original = _get_types_order(owner_client, main_board, main_space)
    _reorder_and_check(
        owner_client, main_board, main_space,
        type_id=original[0], from_index=0, to_index=to_index, expected_index=-1,
    )
