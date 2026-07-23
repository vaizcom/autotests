import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import (
    get_board_endpoint,
    reorder_board_type_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.fixture(scope="module")
def first_type_id(owner_client, main_space, main_board):
    """_id первого типа на main_board."""
    resp = owner_client.post(**get_board_endpoint(main_board, main_space))
    assert resp.status_code == 200, resp.text
    return resp.json()["payload"]["board"]["typesList"][0]["_id"]


@allure.parent_suite("Board Service")
@allure.suite("Access board")
@allure.sub_suite("ReorderBoardType")
@pytest.mark.parametrize(
    "client_fixture",
    [
        pytest.param("owner_client", id="owner"),
        pytest.param("manager_client", id="manager"),
    ],
)
@allure.title("ReorderBoardType: {client_fixture} → 200")
def test_reorder_type_allowed(
    request, client_fixture, main_space, main_board, first_type_id,
):
    """Пользователи с правами управления бордой могут менять порядок типов."""
    client = request.getfixturevalue(client_fixture)

    with allure.step("Перемещаем тип на ту же позицию (без изменений)"):
        resp = client.post(**reorder_board_type_endpoint(
            board_id=main_board, space_id=main_space,
            board_type_id=first_type_id, from_index=0, to_index=0,
        ))

    with allure.step("Проверяем 200"):
        assert resp.status_code == 200, f"Ожидали 200, получили: {resp.status_code}"


@allure.parent_suite("Board Service")
@allure.suite("Access board")
@allure.sub_suite("ReorderBoardType")
@pytest.mark.parametrize(
    "client_fixture",
    [
        pytest.param("member_client", id="member"),
        pytest.param("guest_client", id="guest"),
        pytest.param("client_with_access_only_in_space", id="space_client"),
        pytest.param("client_with_access_only_in_project", id="project_client"),
        pytest.param("foreign_client", id="foreign_client"),
    ],
)
@allure.title("ReorderBoardType: {client_fixture} → 403 AccessDenied")
def test_reorder_type_denied(
    request, client_fixture, main_space, main_board, first_type_id,
):
    """Пользователи без прав управления бордой не могут менять порядок типов."""
    client = request.getfixturevalue(client_fixture)

    with allure.step("Пытаемся переместить тип"):
        resp = client.post(**reorder_board_type_endpoint(
            board_id=main_board, space_id=main_space,
            board_type_id=first_type_id, from_index=0, to_index=0,
        ))

    with allure.step("Проверяем 403 AccessDenied"):
        assert resp.status_code == 403, f"Ожидали 403, получили: {resp.status_code}"
        assert resp.json()["error"]["code"] == "AccessDenied"
