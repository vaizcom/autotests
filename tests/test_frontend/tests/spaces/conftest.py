import pytest
import requests

from tests.test_frontend.conftest import API_URL


def _delete_space(token: str, space_id: str) -> None:
    requests.post(
        f"{API_URL}/RemoveSpace",
        headers={
            "Authorization": f"Bearer {token}",
            "Cookie": f"_t={token}",
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
        json={"spaceId": space_id},
        timeout=30,
        verify=False,
    )


@pytest.fixture()
def cleanup_space(api_token):
    """После теста удаляет созданные Space через API."""
    ids = []
    yield ids
    for space_id in ids:
        _delete_space(api_token, space_id)
