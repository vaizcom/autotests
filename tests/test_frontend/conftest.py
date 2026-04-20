import pytest
import urllib3

from config.generators import generate_project_name, generate_slug
from config.settings import API_URL, MAIN_SPACE_ID
from tests.core.auth import get_token
from tests.core.client import APIClient
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    create_project_endpoint,
)
from tests.test_frontend.core.settings import BASE_URL, FRONTEND_EMAIL, FRONTEND_PASSWORD

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@pytest.fixture(scope="session")
def api_client():
    return APIClient(base_url=API_URL, token=get_token('main'))


@pytest.fixture(scope="session")
def auth_state(playwright):
    browser = playwright.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(f"{BASE_URL}/auth/sign-in")
    page.get_by_role("textbox", name="Email").fill(FRONTEND_EMAIL)
    page.get_by_role("textbox", name="Password").fill(FRONTEND_PASSWORD)
    page.get_by_role("button", name="Continue with Email").click()
    page.wait_for_load_state("networkidle")
    state = context.storage_state()
    context.close()
    browser.close()
    return state


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, auth_state):
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "storage_state": auth_state,
    }


@pytest.fixture(scope="session")
def main_space():
    """Основной space для UI тестов."""
    assert MAIN_SPACE_ID, "Переменная окружения MAIN_SPACE_ID не задана"
    return MAIN_SPACE_ID


@pytest.fixture(scope="module")
def ui_project(api_client, main_space):
    """Создаёт project через API в main_space. Удаляется после модуля."""
    name = generate_project_name()
    slug = generate_slug()
    resp = api_client.post(**create_project_endpoint(
        name=name,
        slug=slug,
        color="blue",
        icon="Dot",
        description="UI test project",
        space_id=main_space,
    ))
    assert resp.status_code == 200, f"Ошибка создания project: {resp.text}"
    project_id = resp.json()['payload']['project']['_id']

    yield {"id": project_id, "name": name}
