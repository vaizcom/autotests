import allure
import pytest

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("GetHistory Access")
@allure.sub_suite("Positive: GetHistory — доступ по ролям")
@pytest.mark.parametrize("client_fixture", [
    "owner_client",
    "manager_client",
    "member_client",
    "guest_client",
], ids=["owner", "manager", "member", "guest"])
def test_get_history_roles_with_access(request, main_space, main_project, client_fixture):
    """Owner, Manager, Member, Guest имеют доступ к истории проекта."""
    client = request.getfixturevalue(client_fixture)

    allure.dynamic.title(f"GetHistory: {client_fixture} запрашивает историю проекта → 200")

    with allure.step(f"Отправляем POST /GetHistory: kind='Project' от имени {client_fixture}"):
        resp = client.post(
            path="/GetHistory",
            json={"kind": "Project", "kindId": main_project},
            headers={"Content-Type": "application/json", "Current-Space-Id": main_space},
        )

    with allure.step("Получаем 200"):
        assert resp.status_code == 200
