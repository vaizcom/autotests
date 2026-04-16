import allure
import pytest

from config.generators import generate_space_name
from test_backend.data.endpoints.Space.space_endpoints import edit_space_endpoint
from test_backend.data.endpoints.file.upload_avatar_endpoint import upload_avatar_endpoint, DUMMY_PNG_CONTENT
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("SPACE_CREATED event")
def test_space_created_event(main_client, space_for_history):
    """
    При создании space генерируется событие SPACE_CREATED с именем space в data.
    """
    space_id = space_for_history["space_id"]
    name = space_for_history["name"]

    assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="SPACE_CREATED",
        expected_data={"name": name},
    )


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("SPACE_RENAMED event")
def test_space_renamed_event(main_client, space_for_history):
    """
    При переименовании space генерируется событие SPACE_RENAMED с новым именем в data.
    """
    space_id = space_for_history["space_id"]
    new_name = generate_space_name()

    with allure.step("Переименовываем space"):
        resp = main_client.post(**edit_space_endpoint(name=new_name, space_id=space_id))
        assert resp.status_code == 200, f"Ошибка переименования space: {resp.text}"

    assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="SPACE_RENAMED",
        expected_data={"name": new_name},
    )


@allure.parent_suite("History Service")
@allure.suite("Space History")
@allure.title("SPACE_AVATAR_CHANGED event")
def test_space_avatar_changed_event(main_client, space_for_history):
    """
    При загрузке аватара для space генерируется событие SPACE_AVATAR_CHANGED.
    """
    space_id = space_for_history["space_id"]

    with allure.step("Загружаем аватар для space"):
        req = upload_avatar_endpoint(
            file_tuple=("avatar.png", DUMMY_PNG_CONTENT, "image/png"),
            kind="Space",
            kind_id=space_id,
        )
        resp = main_client.post(
            req["path"],
            headers={"Current-Space-Id": space_id},
            data=req["data"],
            files=req["files"],
        )
        assert resp.status_code == 200, f"Ошибка загрузки аватара: {resp.text}"

    assert_history_event_exists(
        client=main_client,
        space_id=space_id,
        kind="Space",
        kind_id=space_id,
        expected_event_key="SPACE_AVATAR_CHANGED",
    )
