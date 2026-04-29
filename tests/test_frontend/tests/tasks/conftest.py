import pytest
import requests

from tests.test_frontend.conftest import API_URL


def _delete_board_by_name(token: str, board_name: str, space_id: str) -> None:
    """Находит борду по имени через GetBoards и удаляет её через DeleteBoard."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Cookie": f"_t={token}",
        "Content-Type": "application/json",
        "Current-Space-Id": space_id,
    }
    resp = requests.post(
        f"{API_URL}/GetBoards",
        headers=headers,
        json={},
        timeout=30,
        verify=False,
    )
    if resp.status_code != 200:
        return
    boards = resp.json().get("payload", {}).get("boards", [])
    for board in boards:
        if board.get("name") == board_name:
            requests.post(
                f"{API_URL}/DeleteBoard",
                headers=headers,
                json={"boardId": board["_id"], "board_name": board_name},
                timeout=30,
                verify=False,
            )


@pytest.fixture()
def cleanup_board(api_token):
    """После теста находит и удаляет борду по имени через API.

    Регистрировать сразу после создания борды:
        cleanup_board.append({"board_name": "...", "space_id": "..."})
    """
    boards = []
    yield boards
    for b in boards:
        _delete_board_by_name(api_token, b["board_name"], b["space_id"])
