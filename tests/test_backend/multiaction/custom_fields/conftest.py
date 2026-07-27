import uuid

import pytest
from config.generators import generate_object_id
from test_backend.data.endpoints.Board.board_endpoints import create_board_custom_field_endpoint
from test_backend.task_service.utils import get_member_profile


@pytest.fixture(scope="module")
def _cf_suffix():
    """Уникальный суффикс для имён кастом филдов — генерируется один раз на модуль."""
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="module")
def text_field_id(owner_client, main_space, temp_board_in_main, _cf_suffix):
    """Text кастом филд на temp борде."""
    resp = owner_client.post(**create_board_custom_field_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
        name=f"cf_text_{_cf_suffix}", type="Text",
    ))
    assert resp.status_code == 200, resp.text
    return resp.json()["payload"]["customField"]["_id"]


@pytest.fixture(scope="module")
def number_field_id(owner_client, main_space, temp_board_in_main, _cf_suffix):
    """Number кастом филд на temp борде."""
    resp = owner_client.post(**create_board_custom_field_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
        name=f"cf_number_{_cf_suffix}", type="Number",
    ))
    assert resp.status_code == 200, resp.text
    return resp.json()["payload"]["customField"]["_id"]


@pytest.fixture(scope="module")
def checkbox_field_id(owner_client, main_space, temp_board_in_main, _cf_suffix):
    """Checkbox кастом филд на temp борде."""
    resp = owner_client.post(**create_board_custom_field_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
        name=f"cf_checkbox_{_cf_suffix}", type="Checkbox",
    ))
    assert resp.status_code == 200, resp.text
    return resp.json()["payload"]["customField"]["_id"]


@pytest.fixture(scope="module")
def date_field_id(owner_client, main_space, temp_board_in_main, _cf_suffix):
    """Date кастом филд на temp борде."""
    resp = owner_client.post(**create_board_custom_field_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
        name=f"cf_date_{_cf_suffix}", type="Date",
    ))
    assert resp.status_code == 200, resp.text
    return resp.json()["payload"]["customField"]["_id"]


@pytest.fixture(scope="module")
def select_field(owner_client, main_space, temp_board_in_main, _cf_suffix):
    """Select кастом филд с двумя опциями на temp борде."""
    opt_a = generate_object_id()
    opt_b = generate_object_id()
    resp = owner_client.post(**create_board_custom_field_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
        name=f"cf_select_{_cf_suffix}", type="Select",
        options=[
            {"_id": opt_a, "title": "Option A", "color": "red"},
            {"_id": opt_b, "title": "Option B", "color": "blue"},
        ],
    ))
    assert resp.status_code == 200, resp.text
    field_id = resp.json()["payload"]["customField"]["_id"]
    return {"field_id": field_id, "option_a": opt_a, "option_b": opt_b}


@pytest.fixture(scope="module")
def member_field_id(owner_client, main_space, temp_board_in_main, _cf_suffix):
    """Member кастом филд на temp борде."""
    resp = owner_client.post(**create_board_custom_field_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
        name=f"cf_member_{_cf_suffix}", type="Member",
    ))
    assert resp.status_code == 200, resp.text
    return resp.json()["payload"]["customField"]["_id"]


@pytest.fixture(scope="module")
def linked_tasks_field_id(owner_client, main_space, temp_board_in_main, _cf_suffix):
    """TaskRelations кастом филд на temp борде."""
    resp = owner_client.post(**create_board_custom_field_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
        name=f"cf_linked_{_cf_suffix}", type="TaskRelations",
    ))
    assert resp.status_code == 200, resp.text
    return resp.json()["payload"]["customField"]["_id"]


@pytest.fixture(scope="module")
def url_field_id(owner_client, main_space, temp_board_in_main, _cf_suffix):
    """Url кастом филд на temp борде."""
    resp = owner_client.post(**create_board_custom_field_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
        name=f"cf_url_{_cf_suffix}", type="Url",
    ))
    assert resp.status_code == 200, resp.text
    return resp.json()["payload"]["customField"]["_id"]


@pytest.fixture(scope="module")
def estimation_field_id(owner_client, main_space, temp_board_in_main, _cf_suffix):
    """Estimation кастом филд на temp борде."""
    resp = owner_client.post(**create_board_custom_field_endpoint(
        board_id=temp_board_in_main, space_id=main_space,
        name=f"cf_estimation_{_cf_suffix}", type="Estimation",
    ))
    assert resp.status_code == 200, resp.text
    return resp.json()["payload"]["customField"]["_id"]


@pytest.fixture(scope="module")
def owner_member_id(owner_client, main_space):
    """Member ID владельца в main_space."""
    return get_member_profile(owner_client, main_space)


@pytest.fixture(scope="module")
def second_member_id(member_client, main_space):
    """Member ID второго пользователя в main_space."""
    return get_member_profile(member_client, main_space)
