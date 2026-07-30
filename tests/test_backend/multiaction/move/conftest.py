import pytest

from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint


@pytest.fixture(scope="module")
def board_groups(owner_client, main_space, temp_board_in_main):
    """Группы temp_board_in_main — Backlog, Todo, In Progress, Done."""
    resp = owner_client.post(**get_board_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
    ))
    assert resp.status_code == 200, resp.text
    groups = resp.json()["payload"]["board"]["groups"]
    return {g["name"]: g["_id"] for g in groups}
